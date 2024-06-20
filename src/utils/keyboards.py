import types
from typing import Dict, List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from src.db.models.db_models import DBProxyConnection
from src.utils.payment_utils import calculate_payment_amount

def client_main_menu():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        keyboard=[
            [KeyboardButton(text="🌐 My Connections"), KeyboardButton(text="ℹ️ Info")],
            [KeyboardButton(text="💬 Support"), KeyboardButton(text="📜 Agreement")],
            [KeyboardButton(text="💳 Pay")],  # Add a Pay button
            #[KeyboardButton(text="👤 Profile"), KeyboardButton(text="👤 Profile")],
        ]
    )
    return keyboard

def admin_main_menu():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        keyboard=[
            [KeyboardButton(text="🌐 My Connections"), KeyboardButton(text="ℹ️ Info")],
            [KeyboardButton(text="💬 Support"), KeyboardButton(text="📜 Agreement")],
            [KeyboardButton(text="👥 My Clients")]
        ]
    )
    return keyboard

def info_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔎 Proxy Detail", callback_data="info_proxy_details"),
        InlineKeyboardButton("💰 Price", callback_data="info_prices"),
        InlineKeyboardButton("💰 Payment Methods", callback_data="info_payment_methods"),
        InlineKeyboardButton("🤝 Discounts", callback_data="info_discounts"),
        InlineKeyboardButton("⚙️ Features", callback_data="info_features")
    )
    return keyboard

# src/utils/keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

""" def payment_keyboard(proxies, selected_proxies):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for proxy in proxies:
        button_text = f"{'✅' if proxy.id in selected_proxies else '❌'} {proxy.name}"
        callback_data = f"toggle_proxy:{proxy.id}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    
    keyboard.add(InlineKeyboardButton(text="Confirm Payment", callback_data="confirm_payment"))
    return keyboard """
    
# def proxy_payment_keyboard(proxies, selected_proxies=None):
#     selected_proxies = selected_proxies or []
#     keyboard = InlineKeyboardMarkup()
#     for proxy in proxies:
#         label = "✅" if proxy.id in selected_proxies else "❌"
#         text = f"{label} {proxy.name}"
#         callback_data = f"toggle_proxy:{proxy.id}"
#         keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
#     keyboard.add(InlineKeyboardButton("Done", callback_data="done_selecting_proxies"))
#     return keyboard

# # src/utils/keyboards.py
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# def proxy_payment_keyboard(proxies):
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     for proxy in proxies:
#         button_text = f"Pay for {proxy.name}"
#         callback_data = f"pay_proxy:{proxy.id}"
#         keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
#     return keyboard

from typing import Dict, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

CHECK_MARK = '✅'
CROSS_MARK = '❌'

def generate_days_keyboard(
    selected_connection_days: Dict[str, int], total_amount: float,
    current_end_dates: Dict[str, datetime], new_end_dates: Dict[str, datetime],
    connection_logins: Dict[str, str], selected_connection_ids: List[str]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)  # Set row_width to 2 for two-column layout
    
    for connection_id, login in connection_logins.items():
        current_end_date = current_end_dates.get(connection_id, datetime.now())
        new_end_date = new_end_dates.get(connection_id, current_end_date)
        days = selected_connection_days.get(connection_id, 0)
        is_selected = CHECK_MARK if connection_id in selected_connection_ids else CROSS_MARK
        connection_price = calculate_payment_amount(days)  # Assuming this function returns the price for the given days
        button_text = f"{is_selected} {login}: {current_end_date.strftime('%Y-%m-%d')} -> {new_end_date.strftime('%Y-%m-%d')} ({days} days, Price: {connection_price}$)"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f'toggle_connection:{connection_id}'))

    # Define button texts and values
    button_texts = [
        ('-1 month', -30),
        ('+1 month', 30),
        ('-1 week', -7),
        ('+1 week', 7),
        ('-1 day', -1),
        ('+1 day', 1),
    ]

    # Add buttons in two-column format
    for i in range(0, len(button_texts) - 1, 2):
        button_left = InlineKeyboardButton(text=button_texts[i][0], callback_data=f'change_days:{button_texts[i][1]}')
        button_right = InlineKeyboardButton(text=button_texts[i + 1][0], callback_data=f'change_days:{button_texts[i + 1][1]}')
        keyboard.row(button_left, button_right)

    # If there's an odd number of buttons, add the last one centered
    if len(button_texts) % 2 != 0:
        last_button = InlineKeyboardButton(text=button_texts[-1][0], callback_data=f'change_days:{button_texts[-1][1]}')
        keyboard.add(last_button)

    # Add the reset button
    reset_button = InlineKeyboardButton(text="Reset", callback_data="reset_days")
    keyboard.add(reset_button)
    
    # Add the confirm button
    confirm_button = InlineKeyboardButton(text=f"Confirm (Total: {total_amount}$)", callback_data="confirm_period")
    keyboard.add(confirm_button)

    return keyboard




from typing import List, Optional

def generate_connection_selection_keyboard(connections: List[DBProxyConnection], selected_ids: List[str], user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for connection in connections:
        is_selected = '✅' if connection.id in selected_ids else '❌'
        callback_data = f"select_connection_for_payment:{connection.id}:{user_id}"
        button_text = f"{is_selected} {connection.login} ({connection.connection_type})"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    keyboard.add(InlineKeyboardButton(text="Pay", callback_data="pay_selected_connections"))
    return keyboard

def generate_connection_selection_for_period_keyboard(connections: List[DBProxyConnection], selected_ids: List[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for connection in connections:
        is_selected = '✅' if connection.id in selected_ids else '❌'
        callback_data = f"toggle_connection:{connection.id}"
        button_text = f"{is_selected} {connection.login} ({connection.connection_type})"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    return keyboard

# def generate_proxy_keyboard(proxies, selected_proxy_ids):
#     keyboard = InlineKeyboardMarkup()
#     for proxy in proxies:
#         button_text = f"{proxy.name} {'✅' if proxy.id in selected_proxy_ids else ''}"
#         keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"select_proxy:{proxy.id}"))
#     keyboard.add(InlineKeyboardButton(text="Pay", callback_data="pay_selected_proxies"))
#     return keyboard


# def generate_proxy_selection_keyboard(connections: List[DBProxyConnection], selected_ids: list = None) -> InlineKeyboardMarkup:
#     """Generates an inline keyboard for selecting proxies."""
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     selected_ids = selected_ids or []

#     for connection in connections:
#         proxy = connection.proxy
#         button_text = f"{'✅' if connection.id in selected_ids else '❌'} {proxy.name}"
#         callback_data = f"select_proxy:{connection.id}"  # Use connection.id
#         keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

#     keyboard.add(InlineKeyboardButton(text="Pay", callback_data="pay_selected_proxies"))
#     return keyboard

