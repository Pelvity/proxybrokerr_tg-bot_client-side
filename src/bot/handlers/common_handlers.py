from aiogram import types
from datetime import datetime

from src.bot.bot_setup import bot, dp, database
from src.utils.keyboards import info_keyboard, client_main_menu
from src.utils.helpers import agreement_text
from src.utils.proxy_utils import send_proxies, get_user_proxies
from src.services.iproxyService import IProxyManager
from src.services.localtonetService import LocaltonetManager
from src.bot.config import IPROXY_API_KEY, LOCALTONET_API_KEY
from src.db.models.db_models import DBProxy, User
from sqlalchemy.orm.exc import NoResultFound
from src.db.repositories.proxy_repositories import ProxyRepository
from src.db.repositories.user_repositories import UserRepository
from src.db.repositories.connection_repositories import ConnectionRepository 


iproxy_manager = IProxyManager(IPROXY_API_KEY)
localtonet_manager = LocaltonetManager(LOCALTONET_API_KEY)

@dp.message_handler(lambda message: message.text == "ℹ️ Info")
async def info_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text="Select an option:", reply_markup=info_keyboard())

@dp.message_handler(lambda message: message.text == "📜 Agreement")
async def agreement_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=agreement_text(), reply_markup=client_main_menu())


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
        
        
# @dp.message_handler(lambda message: message.text == "🌐 My Connections")
# async def my_proxy_command(message: types.Message):
#     user_id = message.from_user.id
#     user_username = message.from_user.username
#     first_name = message.from_user.first_name
#     last_name = message.from_user.last_name

#     with database.connect() as session:  # Session opened here
#         # Pass all user data as keyword arguments to get_or_create
#         user, created = User.get_or_create(
#             session=session,
#             telegram_user_id=user_id,
#             username=user_username,
#             first_name=first_name,
#             last_name=last_name,
#             joined_at=datetime.now(),
#             telegram_chat_id=message.chat.id
#         )

#         if not created:
#             # Update existing user's data
#             user.username = user_username
#             user.first_name = first_name
#             user.last_name = last_name
#             # No need to add again - it's already tracked by the session
#             session.commit()  

#         # Access and use user_proxies within the session scope
#         user_proxies = get_user_proxies(user.username, user.telegram_chat_id, user.telegram_user_id)

#         if not user_proxies:
#             await bot.send_message(chat_id=message.chat.id, 
#                                    text="You have no proxies\nBuy it directly:\nhttps://t.me/proxybrokerr")
#         else:
#             await send_proxies(message.chat.id, user_proxies)
#      # Session is automatically closed here
