from aiogram import types
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext

from src.bot.bot_setup import dp
from src.services.payment_service import initiate_payment, confirm_payment, decline_payment, process_payment,send_payment_notification_to_admin
from src.utils.keyboards import generate_days_keyboard, generate_proxy_keyboard
from src.db.models.db_models import User, Payment, DBProxy
from src.utils.payment_utils import send_payment_confirmation_message_to_admin, calculate_payment_amount, update_selected_proxies
from aiogram.dispatcher.filters import Command, Text
from src.utils.proxy_utils import get_user_proxies

selected_proxy_ids = []

@dp.callback_query_handler(lambda c: c.data.startswith('select_proxy:'))
async def handle_select_proxy_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, proxy_id = callback_query.data.split(':')
    proxy_id = int(proxy_id)

    async with state.proxy() as data:
        selected_proxy_ids = data.get('selected_proxy_ids', [])
        selected_proxy_ids = update_selected_proxies(proxy_id, selected_proxy_ids)
        data['selected_proxy_ids'] = selected_proxy_ids

    proxies = get_user_proxies(callback_query.from_user.username, callback_query.message.chat.id, callback_query.from_user.id)
    updated_keyboard = generate_proxy_keyboard(proxies, selected_proxy_ids)
    await callback_query.message.edit_reply_markup(reply_markup=updated_keyboard)

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'pay_selected_proxies')
async def handle_pay_selected_proxies_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        selected_proxy_ids = data.get('selected_proxy_ids', [])

    if selected_proxy_ids:
        # Display the keyboard for selecting the payment period
        keyboard = generate_days_keyboard(30)  # Default to 30 days
        await callback_query.message.answer("Select the period of rent extension:", reply_markup=keyboard)
    else:
        await callback_query.answer("Please select at least one proxy.")

        # Clear the selected proxy IDs
        async with state.proxy() as data:
            data['selected_proxy_ids'] = []

        proxies = get_user_proxies(callback_query.from_user.username, callback_query.message.chat.id, callback_query.from_user.id)
        updated_keyboard = generate_proxy_keyboard(proxies, [])
        await callback_query.message.edit_reply_markup(reply_markup=updated_keyboard)

    
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_payment:'))
async def handle_confirm_payment_callback(callback_query: types.CallbackQuery):
    _, payment_id = callback_query.data.split(':')
    payment = Payment.get(Payment.id == payment_id)

    if payment.status != 'confirmed':
        await confirm_payment(int(payment_id))
        await send_payment_notification_to_admin(payment, 'confirmed')
    
    # Update the button text to mark it as clicked
    message_id = payment.admin_message_id
    markup = callback_query.message.reply_markup
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data == f"confirm_payment:{payment_id}":
                button.text = f"Confirm Payment {payment_id} ✅"
            elif button.callback_data == f"decline_payment:{payment_id}":
                button.text = f"Decline Payment {payment_id}"
    
    await callback_query.message.edit_reply_markup(reply_markup=markup)
    await callback_query.answer("Payment confirmed.")

@dp.callback_query_handler(lambda c: c.data.startswith('decline_payment:'))
async def handle_decline_payment_callback(callback_query: types.CallbackQuery):
    _, payment_id = callback_query.data.split(':')
    payment = Payment.get(Payment.id == payment_id)

    if payment.status != 'declined':
        await decline_payment(int(payment_id))
        await send_payment_notification_to_admin(payment, 'declined')
    
    # Update the button text to mark it as clicked
    message_id = payment.admin_message_id
    markup = callback_query.message.reply_markup
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data == f"decline_payment:{payment_id}":
                button.text = f"Decline Payment {payment_id} ❌"
            elif button.callback_data == f"confirm_payment:{payment_id}":
                button.text = f"Confirm Payment {payment_id}"
    
    await callback_query.message.edit_reply_markup(reply_markup=markup)
    await callback_query.answer("Payment declined.")
@dp.callback_query_handler(lambda c: c.data.startswith('select_period:'))
async def handle_period_selection_callback(callback_query: types.CallbackQuery):
    global selected_proxy_ids
    _, days = callback_query.data.split(':')
    days = int(days)
    await callback_query.answer()

    # Update the keyboard with the new number of days
    keyboard = generate_days_keyboard(days)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

from src.db.repositories.payment_repositories import PaymentRepository
from src.db.database import Database
from src.bot.config import SECRET_NAME, REGION_NAME, DATABASE_NAME, DATABASE_HOST
#database = Database(SECRET_NAME, REGION_NAME, DATABASE_NAME, DATABASE_HOST)
database = dp.get('database')
from aiogram.dispatcher import FSMContext

# ...

@dp.callback_query_handler(lambda c: c.data.startswith('confirm_period:'))
async def handle_period_confirmation_callback(callback_query: types.CallbackQuery, state: FSMContext):
    global selected_proxy_ids
    _, days = callback_query.data.split(':')
    days = int(days)
    await callback_query.answer()

    user_id = callback_query.from_user.id

    # Check if the user exists in the database
    try:
        user = User.get(User.telegram_user_id == user_id)
    except User.DoesNotExist:
        await callback_query.message.answer("User not found. Please register first.")
        return

    selected_proxy_ids = [int(proxy_id) for proxy_id in selected_proxy_ids]
    selected_proxies = DBProxy.select().where(DBProxy.id.in_(selected_proxy_ids))

    total_amount = 0
    for proxy in selected_proxies:
        amount = calculate_payment_amount(days)
        total_amount += amount

    # Prompt the user to enter the transaction ID (TXID)
    await callback_query.message.answer("Please enter the transaction ID (TXID):")

    # Store the necessary data in the state
    await state.update_data(user_id=user_id, selected_proxy_ids=selected_proxy_ids, days=days, total_amount=total_amount)

    # Register the next step handler to wait for the user's message
    await state.set_state("waiting_for_txid")


async def handle_txid_input(message: types.Message, state: FSMContext):
    txid = message.text
    user_id = message.from_user.id

    # Retrieve the stored data from the state
    data = await state.get_data()
    selected_proxy_ids = data.get("selected_proxy_ids")
    days = data.get("days")
    total_amount = data.get("total_amount")

    user = User.get(User.telegram_user_id == user_id)
    selected_proxies = DBProxy.select().where(DBProxy.id.in_(selected_proxy_ids))

    payment_repo = PaymentRepository(database)
    payments = await payment_repo.create_payment(user, total_amount, 'pending', selected_proxies)

    if payments:
        for payment in payments:
            proxy = payment.proxy
            start_date = proxy.expiration_date.date()
            end_date = start_date + timedelta(days=days)
            payment.start_date = start_date
            payment.end_date = end_date
            payment.days = days
            payment.txid = txid
            payment.save()

        await send_payment_confirmation_message_to_admin(payments, txid, days)
        await message.answer("Payment initiated. Please wait for confirmation.")
    else:
        await message.answer("Failed to initiate payment.")

    # Reset the state
    await state.finish()



# Register the message handler for handling TXID input
dp.register_message_handler(handle_txid_input, state="waiting_for_txid")

