# src/handlers/client_handlers.py
from aiogram import types
from ..bot.bot_setup import bot, dp
from ..utils.helpers import forward_message_to_seller
from ..bot.config import ADMIN_CHAT_ID

@dp.message_handler(lambda message: message.chat.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT)
async def handle_client_message(message: types.Message):
    await forward_message_to_seller(message)