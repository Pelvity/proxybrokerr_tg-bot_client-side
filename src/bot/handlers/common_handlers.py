from aiogram import types
import datetime

from src.bot.bot_setup import bot, dp
from src.utils.keyboards import info_keyboard, client_main_menu
from src.utils.helpers import agreement_text
from src.utils.proxy_utils import send_proxies
from src.services.iproxyService import IProxyManager
from src.services.localtonetService import LocaltonetManager
from src.bot.config import IPROXY_API_KEY, LOCALTONET_API_KEY
from src.db.models.db_models import Proxy, User

iproxy_manager = IProxyManager(IPROXY_API_KEY)
localtonet_manager = LocaltonetManager(LOCALTONET_API_KEY)

@dp.message_handler(lambda message: message.text == "ℹ️ Info")
async def info_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text="Select an option:", reply_markup=info_keyboard())

@dp.message_handler(lambda message: message.text == "📜 Agreement")
async def agreement_command(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=agreement_text(), reply_markup=client_main_menu())

@dp.message_handler(lambda message: message.text == "🌐 My Proxy")
async def my_proxy_command(message: types.Message):
    user_username = message.from_user.username
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Check if the user exists in the database
    user, created = User.get_or_create(
        id=user_id,
        defaults={
            'username': user_username,
            'first_name': first_name,
            'last_name': last_name,
            'joined_at': datetime.now()
        }
    )

    # Retrieve the user's proxy connections from the database based on the username
    user_connections = Proxy.select().where(Proxy.name.contains(user_username))

    # Link the proxy connections to the user
    for connection in user_connections:
        connection.user = user
        connection.save()

    if not user_connections:
        await bot.send_message(chat_id=message.chat.id, text="You have no proxies\nBuy it directly:\nhttps://t.me/proxybrokerr")
    else:
        await send_proxies(message.chat.id, user_connections)

