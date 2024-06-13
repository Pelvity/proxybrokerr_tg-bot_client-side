from aiogram import types
from functools import partial
from aiogram.dispatcher.filters import Command, Text
from src.bot.bot_setup import bot, dp, database
from src.utils.keyboards import info_keyboard, client_main_menu
from src.utils.helpers import agreement_text
from src.utils.proxy_utils import send_proxies, get_user_proxies


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
    
@dp.message_handler(lambda message: message.text == "ℹ️ Info")
async def info_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text="Select an option:", reply_markup=info_keyboard())
    

@dp.message_handler(lambda message: message.text == "📜 Agreement")
async def agreement_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=agreement_text(), reply_markup=client_main_menu())
    
@dp.message_handler(lambda message: message.text == "💬 Support")
async def agreement_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text="Just type your question in this chat\nПросто напишите свой вопрос в этот чат\nПросто напишіть своє питання у цей чат", reply_markup=client_main_menu())

@dp.message_handler(lambda message: message.text == "🌐 My Connections")
async def my_proxy_command(message: types.Message):
    # user_id = message.from_user.id
    # user_username = message.from_user.username
    # first_name = message.from_user.first_name
    # last_name = message.from_user.last_name

    with database.get_session() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_or_create_user(message) # Get or create the user
        
        #proxy_repository = ProxyRepository(session)
        #user_proxies = proxy_repository.get_user_proxies(user.id)
        connection_repository = ConnectionRepository(session)
        user_connections = connection_repository.get_user_connections(user.id)

    if not user_connections:
        await bot.send_message(
            chat_id=message.chat.id, 
            text="You have no proxies\nBuy it directly:\nhttps://t.me/proxybrokerr"
        )
    else:
        await send_proxies(message.chat.id, user_connections)


@dp.callback_query_handler(lambda c: c.data.startswith('connection_'))
async def handle_connection_callback(callback_query: types.CallbackQuery):
    connection_id = str(callback_query.data.split('_')[1])
    
    with database.get_session() as session:
        connection_repository = ConnectionRepository(session)
        connection = connection_repository.get_connection_by_id(connection_id)
        
    if connection:
        detail_text = (
            f"`\n"
            f"{connection.login}\n\n"
            f"{connection.host}:{connection.port}:{connection.login}:{connection.password}\n"
            f"Host: {connection.host}\n"
            f"Port: {connection.port}\n"
            f"Login: {connection.login}\n"
            f"Password: {connection.password}\n"
            f"Expiration Date: {connection.expiration_date.strftime('%d/%m/%Y')}\n"
            f"Days Left: {(connection.expiration_date - datetime.now()).days} days\n"
            f"`"
        )
        await bot.send_message(chat_id=callback_query.message.chat.id, text=detail_text, parse_mode='Markdown')
    else:
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Connection not found.")

    await bot.answer_callback_query(callback_query.id)  # Acknowledge the callback query


 
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
            
            

@dp.message_handler(lambda message: message.text == "👤 Profile")
async def info_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text="Your Profile", reply_markup=client_main_menu())
