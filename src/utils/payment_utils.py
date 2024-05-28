from aiogram import Bot, types
from src.bot.config import ADMIN_CHAT_ID
from datetime import timedelta

async def send_payment_confirmation_message_to_admin(payment_list, txid, days):
    bot = Bot.get_current()

    if not payment_list:
        return

    message_text = "Payment(s) received:\n\n"

    for payment in payment_list:
        proxy = payment.proxy
        message_text += f"Payment ID: {payment.id}\n"
        message_text += f"Amount: {payment.amount}\n"
        message_text += f"User: {payment.user.username}\n"
        message_text += f"Proxy ID: {proxy.id}\n"
        message_text += f"Proxy Name: {proxy.name}\n"
        message_text += f"Current Expiration Date: {proxy.expiration_date.strftime('%d/%m/%Y')}\n"
        message_text += f"New Expiration Date: {(proxy.expiration_date + timedelta(days=days)).strftime('%d/%m/%Y')}\n\n"

    message_text += f"Transaction ID (TXID): {txid}\n\n"
    message_text += "Confirm or Decline each payment?"

    markup = types.InlineKeyboardMarkup()
    for payment in payment_list:
        confirm_button = types.InlineKeyboardButton(f"Confirm Payment {payment.id}", callback_data=f"confirm_payment:{payment.id}")
        decline_button = types.InlineKeyboardButton(f"Decline Payment {payment.id}", callback_data=f"decline_payment:{payment.id}")
        
        if payment.status == 'confirmed':
            confirm_button.text += " ✅"
        elif payment.status == 'declined':
            decline_button.text += " ❌"
        
        markup.add(confirm_button, decline_button)

    admin_message = await bot.send_message(ADMIN_CHAT_ID, message_text, reply_markup=markup)

    # Save the admin message ID in each Payment object
    for payment in payment_list:
        payment.admin_message_id = admin_message.message_id
        payment.save()

async def send_payment_status_message_to_user(user, payment):
    bot = Bot.get_current()
    if payment.status == 'confirmed':
        message_text = f"Your payment of {payment.amount} has been confirmed for the following proxy:\n"
        message_text += f"- {payment.proxy.name} (New expiration date: {payment.proxy.expiration_date.strftime('%d/%m/%Y')})\n"
    elif payment.status == 'declined':
        message_text = f"Your payment of {payment.amount} for the following proxy has been declined:\n"
        message_text += f"- {payment.proxy.name}\n"
    else:
        message_text = f"The status of your payment of {payment.amount} is {payment.status}."
    await bot.send_message(user.telegram_chat_id, message_text)

async def send_payment_notification_to_admin(payment, status):
    admin_chat_id = ADMIN_CHAT_ID
    bot = Bot.get_current()

    message_text = f"Payment {status.capitalize()}:\n"
    message_text += f"User ID: {payment.user.id}\n"
    message_text += f"Username: {payment.user.username}\n"
    message_text += f"Service Name: {payment.proxy.service_name}\n"
    message_text += f"Connection ID: {payment.proxy.auth_token}\n"
    message_text += f"Connection Name: {payment.proxy.name}\n"
    message_text += f"Payment Amount: {payment.amount}\n"

    if status == 'approved':
        message_text += f"Start Date: {payment.start_date.strftime('%d/%m/%Y')}\n"
        message_text += f"End Date: {payment.end_date.strftime('%d/%m/%Y')}\n"

    # Send the payment notification as a reply to the original admin message
    await bot.send_message(admin_chat_id, message_text, reply_to_message_id=payment.admin_message_id)


def calculate_payment_amount(days):
    # Define the prices for different durations
    price_per_day = 3
    price_per_week = 15
    price_per_month = 50

    # Calculate the payment amount based on the number of days
    if days >= 30:
        return price_per_month * (days // 30)
    elif days >= 7:
        return price_per_week * (days // 7)
    else:
        return price_per_day * days

def get_payment_id_from_callback(callback_query: types.CallbackQuery):
    _, payment_id = callback_query.data.split(":")
    return int(payment_id)


def update_selected_proxies(proxy_id, selected_proxy_ids):
    if proxy_id in selected_proxy_ids:
        selected_proxy_ids.remove(proxy_id)
    else:
        selected_proxy_ids.append(proxy_id)
    return selected_proxy_ids
