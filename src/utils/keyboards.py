from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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

def payment_keyboard(proxies, selected_proxies):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for proxy in proxies:
        button_text = f"{'✅' if proxy.id in selected_proxies else '❌'} {proxy.name}"
        callback_data = f"toggle_proxy:{proxy.id}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    
    keyboard.add(InlineKeyboardButton(text="Confirm Payment", callback_data="confirm_payment"))
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

