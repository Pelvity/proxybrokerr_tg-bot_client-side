from aiogram import types
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.bot.bot_setup import dp, database
from src.db.repositories.payment_repositories import PaymentRepository
from src.db.repositories.user_repositories import UserRepository
from src.utils.keyboards import generate_connection_selection_keyboard, generate_days_keyboard
from src.db.models.db_models import Payment, DBProxy
from src.utils.payment_utils import calculate_total_payment_amount, send_payment_confirmation_message_to_admin, calculate_payment_amount, send_payment_notification_to_admin
from src.utils.proxy_utils import get_user_connections
from src.db.repositories.connection_repositories import ConnectionRepository
from src.db.repositories.user_repositories import UserRepository
from src.utils.keyboards import generate_days_keyboard, generate_proxy_selection_keyboard
from aiogram.dispatcher.filters import Text
import logging

class PaymentStates(StatesGroup):
    waiting_for_txid = State()

@dp.callback_query_handler(Text(startswith='select_connection:'))
async def handle_select_connection_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, connection_id, _ = callback_query.data.split(':')  # Ignore the user_id in the callback data
    connection_id = str(connection_id)  # Connection IDs are strings

    async with state.proxy() as data:
        user_id = data.get('user_id')  # Retrieve user_id from state data
        if not user_id:
            logging.error("User ID is missing in state data.")
            await callback_query.answer("An error occurred. Please try again.")
            return

        selected_connection_ids = data.get('selected_connection_ids', [])
        if connection_id in selected_connection_ids:
            selected_connection_ids.remove(connection_id)
        else:
            selected_connection_ids.append(connection_id)
        data['selected_connection_ids'] = selected_connection_ids

    try:
        with database.get_session() as session:
            connection_repository = ConnectionRepository(session)
            user_connections = connection_repository.get_user_connections(user_id)  # Use user_id to get connections
        updated_keyboard = generate_connection_selection_keyboard(user_connections, selected_connection_ids, user_id=user_id)  # Pass user_id to the keyboard generator
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
            types.InlineKeyboardButton(text="Bank Transfer", callback_data="payment_method:bank_transfer")
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
        days = 30  # Default to 30 days

    keyboard = generate_days_keyboard(days)
    await state.update_data(days=days)

    await callback_query.message.answer(
        "Select the rent period:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith('select_period:'))
async def handle_period_selection_callback(callback_query: types.CallbackQuery, state: FSMContext):
    days = int(callback_query.data.split(':')[1])
    await state.update_data(days=days)

    keyboard = generate_days_keyboard(days)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('confirm_period:'))
async def handle_period_confirmation_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        days = data.get('days')
        selected_connection_ids = data.get('selected_connection_ids', [])

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

        total_amount, payment_items = calculate_total_payment_amount(selected_connections, days)

    await state.update_data(
        user_id=user_id,
        selected_connection_ids=selected_connection_ids,
        days=days,
        total_amount=total_amount
    )

    await callback_query.message.answer(
        f"Total amount for {days} days: {total_amount}. "
        "Please enter the transaction ID (TXID):"
    )
    await PaymentStates.waiting_for_txid.set()
    await callback_query.answer()

@dp.message_handler(state=PaymentStates.waiting_for_txid)
async def handle_txid_input(message: types.Message, state: FSMContext):
    txid = message.text
    async with state.proxy() as data:
        user_id = data.get("user_id")
        payment_method = data.get("payment_method")
        telegram_user_id = message.from_user.id
        selected_connection_ids = data.get("selected_connection_ids")
        days = data.get("days")
        total_amount = data.get("total_amount")

    with database.get_session() as session:
        payment_repository = PaymentRepository(session)
        connection_repository = ConnectionRepository(session)
        user_repository = UserRepository(session)

        user = user_repository.get_user_by_telegram_user_id(telegram_user_id)
        if not user:
            await message.answer("User not found.")
            await state.finish()
            return

        selected_connections = [
            connection_repository.get_connection_by_id(connection_id)
            for connection_id in selected_connection_ids
        ]
        payment_items = [
            (connection, calculate_payment_amount(days))
            for connection in selected_connections
        ]

        payments = payment_repository.create_payments(user, payment_items, txid, days, payment_method)

        if payments:
            await send_payment_confirmation_message_to_admin(payments, txid, days)
            await message.answer("Payment initiated. Please wait for confirmation.")
        else:
            await message.answer("Failed to initiate payment.")

    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('confirm_payment:'))
async def handle_confirm_payment_callback(callback_query: types.CallbackQuery):
    _, payment_id = callback_query.data.split(':')

    with database.get_session() as session:
        payment_repository = PaymentRepository(session)
        payment = payment_repository.get_payment_by_id(int(payment_id))

        if payment:
            payment_repository.confirm_payment(payment)

            # Update the original message with icons and make the reply
            message_text = callback_query.message.text
            updated_message_text = f"{message_text}\n\n✅ Payment {payment_id} confirmed."
            keyboard = callback_query.message.reply_markup

            # Update the button to show the confirmation
            for row in keyboard.inline_keyboard:
                for button in row:
                    if button.callback_data == f'confirm_payment:{payment_id}':
                        button.text = f'✅ {button.text}'
                    elif button.callback_data == f'decline_payment:{payment_id}':
                        button.text = f'❌ {button.text}'

            await callback_query.message.edit_text(updated_message_text, reply_markup=keyboard)

            await callback_query.message.reply(f"Payment {payment_id} confirmed.")
        else:
            await callback_query.message.reply("Payment not found.")

@dp.callback_query_handler(lambda c: c.data.startswith('decline_payment:'))
async def handle_decline_payment_callback(callback_query: types.CallbackQuery):
    _, payment_id = callback_query.data.split(':')

    with database.get_session() as session:
        payment_repository = PaymentRepository(session)
        payment = payment_repository.get_payment_by_id(int(payment_id))

        if payment:
            payment_repository.decline_payment(payment)

            # Update the original message with icons and make the reply
            message_text = callback_query.message.text
            updated_message_text = f"{message_text}\n\n❌ Payment {payment_id} declined."
            keyboard = callback_query.message.reply_markup

            # Update the button to show the confirmation
            for row in keyboard.inline_keyboard:
                for button in row:
                    if button.callback_data == f'confirm_payment:{payment_id}':
                        button.text = f'✅ {button.text}'
                    elif button.callback_data == f'decline_payment:{payment_id}':
                        button.text = f'❌ {button.text}'

            await callback_query.message.edit_text(updated_message_text, reply_markup=keyboard)

            # Reply to the message
            await callback_query.message.reply(f"Payment {payment_id} declined.")
        else:
            await callback_query.message.reply("Payment not found.")

    
# @dp.callback_query_handler(lambda c: c.data.startswith('select_proxy:'))
# async def handle_select_proxy_callback(callback_query: types.CallbackQuery, state: FSMContext):
#     _, proxy_id = callback_query.data.split(':')
#     proxy_id = int(proxy_id)

#     async with state.proxy() as data:
#         selected_proxy_ids = data.get('selected_proxy_ids', [])
#         if proxy_id in selected_proxy_ids:
#             selected_proxy_ids.remove(proxy_id)
#         else:
#             selected_proxy_ids.append(proxy_id)
#         data['selected_proxy_ids'] = selected_proxy_ids

#     # Use ConnectionRepository to get connections
#     with database.get_session() as session:
#         connection_repository = ConnectionRepository(session)
#         user_connections = connection_repository.get_user_connections(callback_query.from_user.id)

#     updated_keyboard = generate_proxy_selection_keyboard(user_connections, selected_proxy_ids)
#     await callback_query.message.edit_reply_markup(reply_markup=updated_keyboard)
#     await callback_query.answer()


# @dp.callback_query_handler(lambda c: c.data == 'pay_selected_proxies')
# async def handle_pay_selected_proxies_callback(callback_query: types.CallbackQuery, state: FSMContext):
#     async with state.proxy() as data:
#         selected_proxy_ids = data.get('selected_proxy_ids', [])

#     if selected_proxy_ids:
#         keyboard = generate_days_keyboard(30)
#         await callback_query.message.answer("Select the period of rent extension:", reply_markup=keyboard)
#     else:
#         await callback_query.answer("Please select at least one proxy.")
#         async with state.proxy() as data:
#             data['selected_proxy_ids'] = []

#         # Use ConnectionRepository to get connections
#         with database.get_session() as session:
#             connection_repository = ConnectionRepository(session)
#             user_connections = connection_repository.get_user_connections(callback_query.from_user.id)

#         updated_keyboard = generate_proxy_selection_keyboard(user_connections, [])
#         await callback_query.message.edit_reply_markup(reply_markup=updated_keyboard)