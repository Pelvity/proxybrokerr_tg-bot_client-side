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