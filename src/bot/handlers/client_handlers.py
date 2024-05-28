from aiogram import types
from functools import partial
from aiogram.dispatcher.filters import Command, Text

from src.bot.bot_setup import dp
from src.utils.keyboards import client_main_menu
from src.utils.proxy_utils import get_user_proxies
from src.db.database import Database
from src.db.repositories.user_repositories import UserRepository
from src.bot.config import SECRET_NAME, REGION_NAME, DATABASE_NAME, DATABASE_HOST, ADMIN_CHAT_ID
from src.utils.helpers import forward_message_to_admin
from src.bot.handlers.payment_handlers import *
from src.utils.payment_utils import *
from src.services.payment_service import *

@dp.message_handler(commands=['start'])
async def admin_start_command(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        await message.reply("Welcome to ProxyHelper!", reply_markup=client_main_menu())

# client_handlers.py
@dp.message_handler(lambda message: message.text == "💳 Pay")
async def handle_pay_command(message: types.Message):
    database = dp.get('database')
    user_repository = UserRepository(database)
    user = await user_repository.get_or_create_user(message)

    if user:
        await user_repository.update_user(user, message)

        proxies = get_user_proxies(user.username, user.telegram_chat_id, user.telegram_user_id)  # Fetch proxies associated with the user
        if proxies:
            keyboard = types.InlineKeyboardMarkup()
            selected_proxy_ids = []  # Keep track of selected proxy IDs
            for proxy in proxies:
                button_text = f"{proxy.name}"
                keyboard.add(types.InlineKeyboardButton(text=button_text, callback_data=f"select_proxy:{proxy.id}"))
            keyboard.add(types.InlineKeyboardButton(text="Pay", callback_data="pay_selected_proxies"))
            message_text = "Select the proxies you want to pay for:"
            await message.answer(message_text, reply_markup=keyboard)
        else:
            await message.answer("You currently have no proxies to pay for.")
    else:
        await message.answer("Failed to retrieve user information.")


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_client_message(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        await forward_message_to_admin(message)
