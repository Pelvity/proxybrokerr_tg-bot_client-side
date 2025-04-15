from aiogram import types
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.bot.bot_setup import dp, database
from src.bot.config import ADMIN_CHAT_ID, PM_BINANCE_USDT_TRC20, PM_PEKAOBANK, PM_PRIVATBANK
from src.db.repositories.payment_repositories import PaymentRepository
from src.db.repositories.user_repositories import UserRepository
from src.utils.keyboards import generate_connection_selection_for_period_keyboard, generate_connection_selection_keyboard, generate_days_keyboard
from src.db.models.db_models import CryptoPayment, Payment
from src.utils.payment_utils import calculate_total_payment_amount, send_payment_confirmation_message_to_admin, calculate_payment_amount, send_payment_status_message_to_user
from src.db.repositories.connection_repositories import ConnectionRepository
import logging

class PaymentStates(StatesGroup):
    waiting_for_txid = State()
    
class AdminPaymentStates(StatesGroup):
    waiting_for_admin_confirmation = State()


# Selecting connections for payment
@dp.callback_query_handler(lambda c: c.data.startswith('select_connection_for_payment:'))
async def handle_select_connection_for_payment_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, connection_id, user_id = callback_query.data.split(':')
    connection_id = str(connection_id)

    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])
        if connection_id in selected_connection_ids:
            selected_connection_ids.remove(connection_id)
        else:
            selected_connection_ids.append(connection_id)
        data['selected_connection_ids'] = selected_connection_ids

    try:
        with database.get_session() as session:
            connection_repository = ConnectionRepository(session)
            user_connections = connection_repository.get_user_connections(user_id)
        updated_keyboard = generate_connection_selection_keyboard(user_connections, selected_connection_ids, user_id)
        await callback_query.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        logging.exception(f"Error handling select connection callback: {e}")
    finally:
        await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'pay_selected_connections')
async def handle_pay_selected_connections_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])

    if selected_connection_ids:
        payment_methods_keyboard = types.InlineKeyboardMarkup()
        payment_methods_keyboard.add(
            types.InlineKeyboardButton(text="Crypto", callback_data="payment_method:crypto"),
            #types.InlineKeyboardButton(text="Bank Transfer", callback_data="payment_method:bank_transfer")
        )
        await callback_query.message.answer("Select the payment method:", reply_markup=payment_methods_keyboard)
    else:
        await callback_query.answer("Please select at least one connection.")

@dp.callback_query_handler(lambda c: c.data.startswith('payment_method:'))
async def handle_payment_method_selection(callback_query: types.CallbackQuery, state: FSMContext):
    payment_method = callback_query.data.split(':')[1]
    await state.update_data(payment_method=payment_method)

    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])
        selected_connection_days = {connection_id: 0 for connection_id in selected_connection_ids}  # Default to 30 days

    with database.get_session() as session:
        connection_repository = ConnectionRepository(session)
        selected_connections = [
            connection_repository.get_connection_by_id(connection_id)
            for connection_id in selected_connection_ids
        ]

        total_amount, payment_items = calculate_total_payment_amount(selected_connections, selected_connection_days)
        current_end_dates = {connection.id: connection.expiration_date for connection in selected_connections}
        connection_logins = {connection.id: connection.login for connection in selected_connections}
        new_end_dates = {connection.id: connection.expiration_date + timedelta(days=selected_connection_days[connection.id]) for connection in selected_connections}

    await state.update_data(
        days=selected_connection_days, total_amount=total_amount,
        current_end_dates=current_end_dates, new_end_dates=new_end_dates,
        connection_logins=connection_logins
    )

    keyboard = generate_days_keyboard(
        selected_connection_days, total_amount, current_end_dates, new_end_dates,
        connection_logins, selected_connection_ids
    )
    await callback_query.message.answer("Select the rent period for each connection:", reply_markup=keyboard)





@dp.callback_query_handler(lambda c: c.data.startswith('select_period:'))
async def handle_period_selection_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, connection_id, days = callback_query.data.split(':')
    connection_id = str(connection_id)
    days = int(days)

    async with state.proxy() as data:
        selected_connection_days = data.get('selected_connection_days', {})
        selected_connection_days[connection_id] = days
        data['selected_connection_days'] = selected_connection_days

    await update_total_price(callback_query, state)


async def update_total_price(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])
        selected_connection_days = data.get('selected_connection_days', {})
        current_end_dates = data.get('current_end_dates', {})
        connection_logins = data.get('connection_logins', {})

    with database.get_session() as session:
        connection_repository = ConnectionRepository(session)
        selected_connections = [
            connection_repository.get_connection_by_id(connection_id)
            for connection_id in selected_connection_ids
        ]

        total_amount, payment_items = calculate_total_payment_amount(selected_connections, selected_connection_days)
        new_end_dates = {
            connection.id: current_end_dates.get(connection.id, datetime.now()) + timedelta(days=selected_connection_days.get(connection.id, 0))
            for connection in selected_connections
        }

    await state.update_data(total_amount=total_amount, current_end_dates=current_end_dates, new_end_dates=new_end_dates)

    keyboard = generate_days_keyboard(
        selected_connection_days, total_amount, current_end_dates, new_end_dates,
        connection_logins, selected_connection_ids
    )
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()







@dp.callback_query_handler(lambda c: c.data.startswith('select_connection_for_period:'))
async def handle_select_connection_for_period_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, connection_id, user_id = callback_query.data.split(':')
    connection_id = str(connection_id)

    async with state.proxy() as data:
        selected_connection_days = data.get('selected_connection_days', {})
        selected_connection_days[connection_id] = selected_connection_days.get(connection_id, 0)
        data['selected_connection_days'] = selected_connection_days

    await update_total_price(callback_query, state)

@dp.callback_query_handler(lambda c: c.data.startswith('change_days:'))
async def handle_change_days_callback(callback_query: types.CallbackQuery, state: FSMContext):
    change_value = int(callback_query.data.split(':')[1])

    async with state.proxy() as data:
        selected_connection_days = data.get('selected_connection_days', {})
        selected_connection_ids = data.get('selected_connection_ids', [])
        for connection_id in selected_connection_ids:
            current_days = selected_connection_days.get(connection_id, 0)
            selected_connection_days[connection_id] = max(0, current_days + change_value)  # Ensure days don't go negative
        data['selected_connection_days'] = selected_connection_days

    await update_total_price(callback_query, state)
    
    
@dp.callback_query_handler(lambda c: c.data.startswith('toggle_connection:'))
async def handle_toggle_connection_callback(callback_query: types.CallbackQuery, state: FSMContext):
    connection_id = callback_query.data.split(':')[1]
    connection_id = str(connection_id)

    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])
        if connection_id in selected_connection_ids:
            selected_connection_ids.remove(connection_id)
        else:
            selected_connection_ids.append(connection_id)
        data['selected_connection_ids'] = selected_connection_ids

        selected_connection_days = data.get('selected_connection_days', {})
        current_end_dates = data.get('current_end_dates', {})
        connection_logins = data.get('connection_logins', {})

        # Ensure new_end_dates contains all necessary data
        new_end_dates = data.get('new_end_dates', {conn_id: current_end_dates.get(conn_id, datetime.now()) for conn_id in connection_logins.keys()})

    with database.get_session() as session:
        connection_repository = ConnectionRepository(session)
        selected_connections = [
            connection_repository.get_connection_by_id(connection_id)
            for connection_id in selected_connection_ids
        ]

        # Update new_end_dates for selected connections
        for connection in selected_connections:
            new_end_dates[connection.id] = current_end_dates[connection.id] + timedelta(days=selected_connection_days.get(connection.id, 0))

    total_amount, payment_items = calculate_total_payment_amount(selected_connections, selected_connection_days)

    keyboard = generate_days_keyboard(
        selected_connection_days, total_amount, current_end_dates, new_end_dates,
        connection_logins, selected_connection_ids
    )
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'reset_days')
async def handle_reset_days_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])
        selected_connection_days = {connection_id: 0 for connection_id in selected_connection_ids}
        data['selected_connection_days'] = selected_connection_days

    await update_total_price(callback_query, state)


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_period'))
async def handle_period_confirmation_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        selected_connection_ids = data.get('selected_connection_ids', [])
        selected_connection_days = data.get('selected_connection_days', {})
        payment_method = data.get('payment_method')

    user_id = callback_query.from_user.id
    with database.get_session() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_user_by_telegram_user_id(user_id)

        if not user:
            await callback_query.message.answer("User not found. Please register first.")
            return

        connection_repository = ConnectionRepository(session)
        selected_connections = [
            connection_repository.get_connection_by_id(connection_id)
            for connection_id in selected_connection_ids
        ]

        total_amount, payment_items = calculate_total_payment_amount(selected_connections, selected_connection_days)

    if total_amount <= 0:
        await callback_query.message.answer("Total amount should be more than 0. Please select valid periods.")
        return

    await state.update_data(
        user_id=user_id,
        selected_connection_ids=selected_connection_ids,
        selected_connection_days=selected_connection_days,
        total_amount=total_amount
    )

    if payment_method == 'crypto':
        payment_details = f"Please send the USDT (TRC20) payment to the following address:\n```\n{PM_BINANCE_USDT_TRC20}\n```\nPlease provide the transaction ID (TXID)."
    elif payment_method == 'bank_transfer':
        payment_details = (
            f"Please transfer the amount to one of the following bank accounts:\n"
            f"PrivatBank:\n```\n{PM_PRIVATBANK}\n```\n"
            f"PekaoBank:\n```\n{PM_PEKAOBANK}\n```\nPlease provide the transaction ID."
        )
    else:
        payment_details = "Unknown payment method."

    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel_payment")
    payment_methods_keyboard = types.InlineKeyboardMarkup().add(cancel_button)

    await callback_query.message.answer(
        f"Total amount for selected periods: {total_amount:.2f}.\n{payment_details}",
        reply_markup=payment_methods_keyboard,
        parse_mode="Markdown"
    )
    await PaymentStates.waiting_for_txid.set()
    await callback_query.answer()
    
@dp.callback_query_handler(lambda c: c.data == 'cancel_payment')
async def handle_cancel_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer("Payment process canceled. You can start again by selecting connections.")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'cancel_payment', state=PaymentStates.waiting_for_txid)
async def handle_cancel_payment_during_txid(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.answer("Payment process canceled. You can start again by selecting connections.")
    await callback_query.answer()


@dp.message_handler(state=PaymentStates.waiting_for_txid)
async def handle_txid_input(message: types.Message, state: FSMContext):
    txid = message.text
    async with state.proxy() as data:
        user_id = data.get("user_id")
        payment_method = data.get("payment_method")
        selected_connection_ids = data.get("selected_connection_ids")
        selected_connection_days = data.get("selected_connection_days")
        total_amount = data.get("total_amount")

    with database.get_session() as session:
        payment_repository = PaymentRepository(session)
        connection_repository = ConnectionRepository(session)
        user_repository = UserRepository(session)

        user = user_repository.get_user_by_telegram_user_id(user_id)
        if not user:
            await message.answer("User not found.")
            await state.finish()
            return

        selected_connections = [
            connection_repository.get_connection_by_id(connection_id)
            for connection_id in selected_connection_ids
        ]
        payment_items = [
            (connection, calculate_payment_amount(selected_connection_days.get(connection.id, 0)))
            for connection in selected_connections
        ]

        payments = []
        for connection, amount in payment_items:
            days = selected_connection_days.get(connection.id, 0)
            end_date = connection.expiration_date + timedelta(days=days)
            payment = Payment(
                user_id=user.id,
                connection_id=connection.id,
                amount=amount,
                start_date=connection.expiration_date,
                end_date=end_date,
                payment_method=payment_method,
                status='pending'
            )
            session.add(payment)
            session.commit()  # Commit to get the payment.id

            if payment_method == 'crypto':
                crypto_payment = CryptoPayment(payment_id=payment.id, txid=txid)
                session.add(crypto_payment)

            payments.append(payment)

        session.commit()  # Commit all changes to the database

        if payments:
            await send_payment_confirmation_message_to_admin(payments, txid, selected_connection_days)
            await message.answer("Payment initiated. Awaiting confirmation. Thank you!")
        else:
            await message.answer("No payments were processed. Please try again.")

        # Clear the state to prevent duplicate payments
        await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_payment:') or c.data.startswith('decline_payment:'))
async def handle_admin_action(callback_query: types.CallbackQuery, state: FSMContext):
    action, payment_id = callback_query.data.split(':')
    
    # Save the action and payment_id in the state
    await state.update_data(action=action, payment_id=payment_id)
    
    # Prompt the admin for confirmation
    await callback_query.message.answer(
        f"Are you sure you want to {action.replace('_', ' ')} payment {payment_id}?",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text="Yes", callback_data="admin_confirm"),
            types.InlineKeyboardButton(text="No", callback_data="admin_cancel")
        )
    )
    await AdminPaymentStates.waiting_for_admin_confirmation.set()


from aiogram import types
from aiogram.dispatcher import FSMContext

from aiogram import types
from aiogram.dispatcher import FSMContext
from src.utils.payment_utils import admin_state_data

@dp.callback_query_handler(state=AdminPaymentStates.waiting_for_admin_confirmation)
async def handle_admin_final_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        action = data.get('action')
        payment_id = data.get('payment_id')

    with database.get_session() as session:
        payment_repository = PaymentRepository(session)
        payment = payment_repository.get_payment_by_id(int(payment_id))

        if not payment:
            await callback_query.message.reply("Payment not found.", reply=True)
            await state.finish()
            return

        if action == "confirm_payment":
            crypto_payment = session.query(CryptoPayment).filter_by(payment_id=int(payment_id)).first()
            if not crypto_payment or not crypto_payment.txid:
                await callback_query.message.reply("TXID not found. Please initiate the payment first.", reply=True)
                return
            try:
                payment_repository.confirm_payment(payment, crypto_payment.txid)
            except ValueError as e:
                await callback_query.message.reply(f"Error: {str(e)}", reply=True)
                return
            decision_text = f"✅ Payment {payment_id} confirmed."
        elif action == "decline_payment":
            payment_repository.decline_payment(payment)
            decision_text = f"❌ Payment {payment_id} declined."

        await send_payment_status_message_to_user(payment.user_payments, payment)

        # Retrieve the stored original message text and append the new decision
        original_message_text = admin_state_data.get('original_message_text', '')

        lines = original_message_text.split('\n')
        new_lines = []
        found_payment_section = False
        for line in lines:
            new_lines.append(line)
            if line.startswith(f"Payment ID: {payment_id}"):
                found_payment_section = True
            if found_payment_section and "New Expiration Date:" in line:
                new_lines.append(f"Decision:\n{decision_text}")
                found_payment_section = False

        updated_message_text = '\n'.join(new_lines)

        # Update the admin_state_data with the new message text
        admin_state_data['original_message_text'] = updated_message_text

        # Create the inline keyboard markup again based on stored payment IDs
        markup = types.InlineKeyboardMarkup()
        payment_ids = admin_state_data.get('payment_ids', [])
        for pid in payment_ids:
            if pid != int(payment_id):  # Skip the current payment to avoid re-processing
                markup.add(
                    types.InlineKeyboardButton(
                        text=f"Confirm Payment {pid}", callback_data=f"confirm_payment:{pid}"
                    ),
                    types.InlineKeyboardButton(
                        text=f"Decline Payment {pid}", callback_data=f"decline_payment:{pid}"
                    ),
                )

        # Edit the message with the new status and retain the inline buttons
        await callback_query.bot.edit_message_text(
            chat_id=admin_state_data['admin_chat_id'],
            message_id=admin_state_data['admin_message_id'],
            text=updated_message_text,
            reply_markup=markup
        )

        await state.finish()

    if callback_query.data == "admin_cancel":
        await callback_query.message.reply("Action cancelled.", reply=True)
        await state.finish()










