from datetime import datetime, timedelta
from aiogram import Bot, types
from src.db.models.db_models import User, DBProxy, Payment
from src.utils.payment_utils import *

async def initiate_payment(user_id):
    user = User.get(User.telegram_user_id == user_id)
    proxies = DBProxy.select().where(DBProxy.user == user)

    # Display the list of proxies for the user to select
    proxy_keyboard = types.InlineKeyboardMarkup(row_width=1)
    selected_proxy_ids = []
    for proxy in proxies:
        button_text = f"{proxy.name} {'✅' if proxy.id in selected_proxy_ids else ''}"
        proxy_keyboard.add(types.InlineKeyboardButton(text=button_text, callback_data=f"select_proxy:{proxy.id}"))
    proxy_keyboard.add(types.InlineKeyboardButton(text="Pay", callback_data="pay_selected_proxies"))

    message = await Bot.get_current().send_message(user.chat_id, "Select the proxies you want to pay for:", reply_markup=proxy_keyboard)

    # Wait for the user to finish selecting proxies
    while True:
        callback_query = await Bot.get_current().wait_for_callback_query(lambda q: q.data.startswith("select_proxy:") or q.data == "pay_selected_proxies")
        if callback_query.data == "pay_selected_proxies":
            break
        _, proxy_id = callback_query.data.split(":")
        proxy_id = int(proxy_id)
        if proxy_id in selected_proxy_ids:
            selected_proxy_ids.remove(proxy_id)
        else:
            selected_proxy_ids.append(proxy_id)
        await callback_query.answer()

        # Update the proxy keyboard with the selected proxies marked
        for row in proxy_keyboard.inline_keyboard:
            for button in row:
                if button.callback_data.startswith("select_proxy:"):
                    _, button_proxy_id = button.callback_data.split(":")
                    button_proxy_id = int(button_proxy_id)
                    button.text = f"{button.text.split(' ')[0]} {'✅' if button_proxy_id in selected_proxy_ids else ''}"

        await message.edit_reply_markup(proxy_keyboard)

    # Prompt the user to choose the period of rent extension
    period_keyboard = types.InlineKeyboardMarkup()
    period_options = [
        ("1 month", 30),
        ("2 months", 60),
        ("3 months", 90),
        ("6 months", 180),
        ("1 year", 365),
    ]
    for text, days in period_options:
        period_keyboard.add(types.InlineKeyboardButton(text=text, callback_data=f"select_period:{days}"))

    await Bot.get_current().send_message(user.chat_id, "Select the period of rent extension:", reply_markup=period_keyboard)

    # Wait for the user to select the period
    callback_query = await Bot.get_current().wait_for_callback_query(lambda q: q.data.startswith("select_period:"))
    _, days = callback_query.data.split(":")
    days = int(days)
    await callback_query.answer()

    # Process the payment for the selected proxies and period
    await process_payment(user_id, selected_proxy_ids, days)

async def confirm_payment(payment_id):
    payment = Payment.get(Payment.id == payment_id)
    if payment.status != 'confirmed':
        payment.status = 'confirmed'
        payment.save()

        # Update the expiration date of the proxy
        proxy = payment.proxy
        proxy.expiration_date = payment.end_date
        proxy.save()

        # Notify the user about the payment confirmation
        await send_payment_status_message_to_user(payment.user, payment)

async def decline_payment(payment_id):
    payment = Payment.get(Payment.id == payment_id)
    if payment.status != 'declined':
        payment.status = 'declined'
        payment.save()

        # Revert the expiration date of the proxy to the current expiration date
        proxy = payment.proxy
        proxy.expiration_date = payment.start_date
        proxy.save()

        # Notify the user about the payment decline
        await send_payment_status_message_to_user(payment.user, payment)

# Define a dictionary for tariff plan prices
TARIFF_PRICES = {
    "day": 3,
    "week": 15,
    "month": 50,
}

import logging
from src.utils.payment_utils import calculate_payment_amount

async def process_payment(user_id, proxy_ids, days):
    user = User.get(User.telegram_user_id == user_id)
    selected_proxies = DBProxy.select().where(DBProxy.id.in_(proxy_ids))

    # Initialize total amount
    total_amount = 0

    # Calculate the payment amount for each selected proxy
    for proxy in selected_proxies:
        try:
            # Calculate the amount for the selected period using the utility function
            amount = calculate_payment_amount(days)
            total_amount += amount
        except ValueError as e:
            logging.exception(f"Error calculating payment: {e}")
            continue  # Optionally handle the error or notify the user/admin

    # Return the total amount and selected proxies
    return total_amount, selected_proxies
