from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

# Button
button_my_proxy = InlineKeyboardButton(
    text="🌐 My Proxy", callback_data="my_proxy")
button_info = InlineKeyboardButton(
    text="ℹ️ Info", callback_data="proxy_info")
button_support = InlineKeyboardButton(
    text="💬 Support", callback_data="proxy_support")
button_agreement = InlineKeyboardButton(
    text="📜 Agreement", callback_data="proxy_agreement")
# Keyboard
keyboard_main = ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=False).add(button_my_proxy).add(button_info).add(button_support).add(button_agreement)


def info_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔎 Proxy Detail", callback_data="main_menu_proxy_details"),
        InlineKeyboardButton("💰 Price", callback_data="main_menu_prices"),
        InlineKeyboardButton("💰 Payment Methods", callback_data="main_menu_payment_methods"),
        InlineKeyboardButton("🤝 Discounts", callback_data="main_menu_discounts"),
        InlineKeyboardButton("⚙️ Features", callback_data="main_menu_features")
    )
    return keyboard
