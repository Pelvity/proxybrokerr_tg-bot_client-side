from typing import Dict, List, Tuple
from aiogram import Bot, types
from datetime import datetime, timedelta
from src.bot.config import ADMIN_CHAT_ID
from src.bot.bot_setup import database
from src.db.models.db_models import DBProxyConnection, Payment
from aiogram.dispatcher import FSMContext

from typing import List, Dict
from aiogram import Bot, types
from datetime import timedelta, datetime
from aiogram.dispatcher import FSMContext

admin_state_data = {}

async def send_payment_confirmation_message_to_admin(payment_list: List[Payment], txid: str, selected_connection_days: Dict[int, int]):
    bot = Bot.get_current()

    if not payment_list:
        return

    message_text = "Payment(s) received:\n\n"

    for payment in payment_list:
        connection = payment.connection
        days = selected_connection_days.get(connection.id, 0)
        new_expiration_date = connection.expiration_date + timedelta(days=days) if connection.expiration_date else datetime.now().date() + timedelta(days=days)
        message_text += f"Payment ID: {payment.id}\n"
        message_text += f"Connection login: {connection.login}\n"
        message_text += f"Amount: {payment.amount}\n"
        message_text += f"User: {payment.user_payments.username}\n"
        message_text += f"Connection ID: {connection.id}\n"
        message_text += f"Current Expiration Date: {connection.expiration_date.strftime('%d/%m/%Y') if connection.expiration_date else 'N/A'}\n"
        message_text += f"New Expiration Date: {new_expiration_date.strftime('%d/%m/%Y')}\n\n"

    message_text += f"Transaction ID (TXID): https://tronscan.org/#/transaction/{txid}\n\n"
    message_text += "Confirm or Decline each payment?"

    admin_chat_id = ADMIN_CHAT_ID
    markup = types.InlineKeyboardMarkup()
    payment_ids = []
    for payment in payment_list:
        payment_ids.append(payment.id)
        markup.add(
            types.InlineKeyboardButton(
                text=f"Confirm Payment {payment.id}", callback_data=f"confirm_payment:{payment.id}"
            ),
            types.InlineKeyboardButton(
                text=f"Decline Payment {payment.id}", callback_data=f"decline_payment:{payment.id}"
            ),
        )

    sent_message = await bot.send_message(admin_chat_id, message_text, reply_markup=markup)

    # Store the message ID, chat ID, original message text, and payment IDs in the shared storage
    admin_state_data['admin_message_id'] = sent_message.message_id
    admin_state_data['admin_chat_id'] = admin_chat_id
    admin_state_data['original_message_text'] = message_text
    admin_state_data['payment_ids'] = payment_ids






async def send_payment_status_message_to_user(user, payment):
    bot = Bot.get_current()
    if payment.status == 'confirmed':
        message_text = f"✅ Payment {payment.id} confirmed.\nConnection: {payment.connection.login}\nPrice: {payment.amount}\nExpiration date: {payment.start_date.strftime('%d/%m/%Y')} -> {payment.end_date.strftime('%d/%m/%Y')}"
    elif payment.status == 'declined':
        message_text = f"❌ Payment {payment.id} declined.\nConnection: {payment.connection.login}\nPrice: {payment.amount}"
    else:
        message_text = f"The status of your payment of {payment.amount} is {payment.status}."
    await bot.send_message(user.telegram_chat_id, message_text)

async def send_final_decision_to_admin(payment, final_status):
    admin_chat_id = ADMIN_CHAT_ID
    bot = Bot.get_current()

    message_text = f"Final decision:\n"
    message_text += f"{final_status} Payment {payment.id}.\n"

    await bot.send_message(admin_chat_id, message_text)

async def send_payment_notification_to_admin(payment, status):
    admin_chat_id = ADMIN_CHAT_ID
    bot = Bot.get_current()

    if status == 'confirmed':
        message_text = f"✅ Payment {payment.id} confirmed.\n"
    else:
        message_text = f"❌ Payment {payment.id} declined.\n"

    message_text += f"User ID: {payment.user.id}\n"
    message_text += f"Username: {payment.user.username}\n"
    message_text += f"Service Name: {payment.connection.proxy.service_name}\n"
    message_text += f"Connection ID: {payment.connection.id}\n"
    message_text += f"Connection Name: {payment.connection.proxy.name}\n"
    message_text += f"Payment Amount: {payment.amount}\n"

    if status == 'confirmed':
        message_text += f"Start Date: {payment.start_date.strftime('%d/%m/%Y')}\n"
        message_text += f"End Date: {payment.end_date.strftime('%d/%m/%Y')}\n"

    await bot.send_message(admin_chat_id, message_text)

def calculate_payment_amount(days):
    # Define the prices for different durations
    price_per_day = 3
    price_per_week = 15
    price_per_month = 50

    # Calculate the number of months, weeks, and remaining days
    months = days // 30
    days_remaining_after_months = days % 30

    weeks = days_remaining_after_months // 7
    days_remaining_after_weeks = days_remaining_after_months % 7

    # Calculate the total cost
    if days < 7:
        total_cost = days * price_per_day
    else:
        total_cost = (months * price_per_month) + (weeks * price_per_week) + (days_remaining_after_weeks * price_per_day)

    return round(total_cost, 2)

def calculate_total_payment_amount(connections: List[DBProxyConnection], days: Dict[str, int]) -> Tuple[float, List[Tuple[DBProxyConnection, float]]]:
    total_amount = 0.0
    payment_items = []
    for connection in connections:
        connection_days = days.get(connection.id, 0)
        amount = calculate_payment_amount(connection_days)
        total_amount += amount
        payment_items.append((connection, amount))
    return total_amount, payment_items

# def get_payment_id_from_callback(callback_query: types.CallbackQuery):
#     _, payment_id = callback_query.data.split(":")
#     return int(payment_id)

# def update_selected_proxies(proxy_id, selected_proxy_ids):
#     if proxy_id in selected_proxy_ids:
#         selected_proxy_ids.remove(proxy_id)
#     else:
#         selected_proxy_ids.append(proxy_id)
#     return selected_proxy_ids
