""" # handlers/start_handler.py

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from src.bot.bot_setup import dp
from src.utils.keyboards import keyboard_main

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Hello! I am Proxy Helper", reply_markup=keyboard_main)
 """
""" from aiogram import types
from functools import partial
from aiogram.dispatcher.filters import Command, Text
from src.utils.helpers import forward_message_to_admin
from src.bot.config import SECRET_NAME, REGION_NAME, DATABASE_NAME, DATABASE_HOST, ADMIN_CHAT_ID

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_client_message(message: types.Message):
    if message.chat.id != ADMIN_CHAT_ID:
        await forward_message_to_admin(message)
 """