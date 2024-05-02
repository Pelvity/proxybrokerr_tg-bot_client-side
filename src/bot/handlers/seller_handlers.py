""" # src/handlers/seller_handlers.py
from aiogram import types
from src.bot.bot_setup import bot, dp
from src.utils.helpers import send_reply_to_client

@dp.message_handler(is_forwarded=True)
async def handle_seller_reply(message: types.Message):
    await send_reply_to_client(message)
 """