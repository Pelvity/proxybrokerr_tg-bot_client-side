from aiogram import types
from functools import partial
from aiogram.dispatcher.filters import Command, Text

#from src.bot.bot_setup import dp, database
from src.db.repositories.proxy_repositories import ProxyRepository
from src.utils.keyboards import client_main_menu, generate_connection_selection_keyboard
from src.utils.proxy_utils import get_user_proxies
from src.db.repositories.user_repositories import UserRepository
from src.bot.config import SECRET_NAME, REGION_NAME, DATABASE_NAME, DATABASE_HOST, ADMIN_CHAT_ID
from src.utils.helpers import forward_message_to_admin
from src.bot.handlers.payment_handlers import *
from src.utils.payment_utils import *
from src.services.payment_service import *


@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID, commands=['start'])
async def admin_start_command(message: types.Message):
    await message.reply("Welcome to ProxyBroker Helper!", reply_markup=client_main_menu())

@dp.message_handler(lambda message: message.text == "💳 Pay")
async def handle_pay_command(message: types.Message, state: FSMContext):
    with database.get_session() as session:
        user_repository = UserRepository(session)
        connection_repository = ConnectionRepository(session)

        user = user_repository.get_or_create_user(message)
        if user is None:
            await message.answer("Failed to retrieve user information.")
            return

        user_repository.update_user(user, message)

        connections = connection_repository.get_user_connections(user.id)
        if connections:
            await state.update_data(selected_connection_ids=[])  # Initialize selected connections
            await state.update_data(user_id=user.id)  # Store user_id in state data
            await state.update_data(telegram_user_id=message.from_user.id) 
            keyboard = generate_connection_selection_keyboard(connections, user_id=user.id)  # Pass user_id to the keyboard generator
            await message.answer("Select the connections you want to pay for:", reply_markup=keyboard)
        else:
            await message.answer("You currently have no connections to pay for.")