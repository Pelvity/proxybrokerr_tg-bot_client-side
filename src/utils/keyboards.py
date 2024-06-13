import types
from typing import List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from src.db.models.db_models import DBProxyConnection

def client_main_menu():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        keyboard=[
            [KeyboardButton(text="🌐 My Proxy"), KeyboardButton(text="ℹ️ Info")],
            [KeyboardButton(text="💬 Support"), KeyboardButton(text="📜 Agreement")],
            [KeyboardButton(text="💳 Pay")]  # Add a Pay button
        ]
    )
    return keyboard

def admin_main_menu():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        keyboard=[
            [KeyboardButton(text="🌐 My Proxy"), KeyboardButton(text="ℹ️ Info")],
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
    
def proxy_payment_keyboard(proxies, selected_proxies=None):
    selected_proxies = selected_proxies or []
    keyboard = InlineKeyboardMarkup()
    for proxy in proxies:
        label = "✅" if proxy.id in selected_proxies else "❌"
        text = f"{label} {proxy.name}"
        callback_data = f"toggle_proxy:{proxy.id}"
        keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    keyboard.add(InlineKeyboardButton("Done", callback_data="done_selecting_proxies"))
    return keyboard

# src/utils/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def proxy_payment_keyboard(proxies):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for proxy in proxies:
        button_text = f"Pay for {proxy.name}"
        callback_data = f"pay_proxy:{proxy.id}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    return keyboard

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_days_keyboard(days: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    days_button = InlineKeyboardButton(text=str(days), callback_data=f'select_period:{days}')
    keyboard.add(days_button)

    button_texts = [
        ('-1 month', -30),
        ('+1 month', 30),
        ('-1 week', -7),
        ('+1 week', 7),
        ('-1 day', -1),
        ('+1 day', 1),
        ('Reset', 0),
    ]

    for text, value in button_texts:
        button = InlineKeyboardButton(text=text, callback_data=f'select_period:{days + value}')
        keyboard.add(button)

    confirm_button = InlineKeyboardButton(text="Confirm", callback_data=f"confirm_period:{days}")
    keyboard.add(confirm_button)

    return keyboard

def generate_proxy_keyboard(proxies, selected_proxy_ids):
    keyboard = InlineKeyboardMarkup()
    for proxy in proxies:
        button_text = f"{proxy.name} {'✅' if proxy.id in selected_proxy_ids else ''}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"select_proxy:{proxy.id}"))
    keyboard.add(InlineKeyboardButton(text="Pay", callback_data="pay_selected_proxies"))
    return keyboard


def generate_proxy_selection_keyboard(connections: List[DBProxyConnection], selected_ids: list = None) -> InlineKeyboardMarkup:
    """Generates an inline keyboard for selecting proxies."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    selected_ids = selected_ids or []

    for connection in connections:
        proxy = connection.proxy
        button_text = f"{'✅' if connection.id in selected_ids else '❌'} {proxy.name}"
        callback_data = f"select_proxy:{connection.id}"  # Use connection.id
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    keyboard.add(InlineKeyboardButton(text="Pay", callback_data="pay_selected_proxies"))
    return keyboard

from typing import List, Optional

CHECK_MARK = '✅'
CROSS_MARK = '❌'

def generate_connection_selection_keyboard(connections: List[DBProxyConnection], selected_ids: Optional[List[str]] = None, user_id: int = None) -> InlineKeyboardMarkup:
    """Generates an inline keyboard for selecting connections."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    selected_ids = selected_ids or []

    for connection in connections:
        proxy = connection.proxy
        is_selected = CHECK_MARK if connection.id in selected_ids else CROSS_MARK
        callback_data = f"select_connection:{connection.id}:{user_id}"  # Include user_id in the callback data
        button_text = f"{is_selected} {proxy.name} ({connection.connection_type})"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    keyboard.add(InlineKeyboardButton(text="Pay", callback_data="pay_selected_connections"))
    return keyboard
