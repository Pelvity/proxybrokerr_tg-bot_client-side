from aiogram import types
from src.bot.bot_setup import bot, dp
from src.utils.helpers import forward_message_to_admin
from src.bot.config import ADMIN_CHAT_ID
from src.utils.keyboards import client_main_menu, proxy_payment_keyboard
from src.utils.proxy_utils import get_all_proxies, get_user_proxies

# /start
@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID, commands=['start'])
async def admin_start_command(message: types.Message):
    await message.reply("Welcome to ProxyHelper!", reply_markup=client_main_menu())
    
# src/bot/handlers/client_handlers.py
from aiogram import types
from src.utils.keyboards import proxy_payment_keyboard
from src.utils.proxy_utils import get_user_proxies

@dp.message_handler(lambda message: message.text == "💳 Pay")
async def handle_pay_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    proxies = get_user_proxies(username, chat_id, user_id)  # Fetch proxies associated with the user
    if proxies:
        keyboard = proxy_payment_keyboard(proxies)
        await message.answer("Select a proxy to pay for:", reply_markup=keyboard)
    else:
        await message.answer("You currently have no proxies to pay for.")


@dp.message_handler(lambda message: message.chat.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY)
async def handle_client_message(message: types.Message):
    await forward_message_to_admin(message)
