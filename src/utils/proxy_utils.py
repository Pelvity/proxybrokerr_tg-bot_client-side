from datetime import datetime
from typing import List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

from src.bot.bot_setup import bot
from src.bot.config import BASE_API_URL, AUTH_HEADER
from src.db.repositories.connection_repositories import ConnectionRepository 
from src.db.models.db_models import User, DBProxy, DBProxyConnection
from src.db.repositories.user_repositories import UserRepository

user_selections = {}  # Store user proxy selections

# async def send_proxies(chat_id: int, proxies: List[DBProxy]):
#     buttons = [
#         InlineKeyboardButton(
#             text=f"{proxy.name} | {proxy.expiration_date.strftime('%d/%m/%Y')} | {proxy.days_left} days left",
#             callback_data=f"proxy_{proxy.service_name}_{proxy.auth_token}_{proxy.id}",  
#         ) 
#         for proxy in proxies
#     ]

#     keyboard = InlineKeyboardMarkup(row_width=1).add(*buttons)
#     await bot.send_message(chat_id=chat_id, text="Your Proxies:", reply_markup=keyboard)


async def send_proxies(chat_id: int, connections: List[DBProxyConnection]):  
    buttons = []
    for connection in connections:
        proxy = connection.proxy 
        days_left = (connection.expiration_date - datetime.now()).days  # Calculate days left
        button_text = (
            f"{connection.login} | "
            f"{connection.expiration_date.strftime('%d/%m/%Y')} | "
            f"{days_left} days left" 
        )
        callback_data = f"connection_{connection.id}"  # Include connection ID

        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        buttons.append(button)

    keyboard = InlineKeyboardMarkup(row_width=1).add(*buttons)
    await bot.send_message(chat_id=chat_id, text="Your Connections:", reply_markup=keyboard)

async def get_connections():
    response = requests.get(f"{BASE_API_URL}/connections", headers=AUTH_HEADER)
    return response.json()["result"]

async def get_connection_info(connection_id):
    response = requests.get(f"{BASE_API_URL}/connections/{connection_id}", headers=AUTH_HEADER)
    return response.json()["result"]

async def get_proxies(connection_id):
    response = requests.get(f"{BASE_API_URL}/connections/{connection_id}/proxies", headers=AUTH_HEADER)
    return response.json()["result"]

def toggle_proxy_selection(user_id, proxy_id):
    """Toggles proxy selection for a user."""
    current_selections = user_selections.get(user_id, set())
    if proxy_id in current_selections:
        current_selections.remove(proxy_id)
    else:
        current_selections.add(proxy_id)
    user_selections[user_id] = current_selections
    return current_selections

def get_selected_proxies(user_id):
    """Returns the set of selected proxy IDs for the user."""
    return user_selections.get(user_id, set())

def process_payment_for_proxies(database, user_id, proxy_ids):  # database injected
    """Processes payment and updates proxy statuses."""
    with database.get_session() as session:
        for proxy_id in proxy_ids:
            proxy = session.query(DBProxy).filter_by(id=proxy_id).first()
            if proxy:
                proxy.active = True
                session.commit()

def get_user_proxies(database, username, chat_id, user_id):
    """Retrieves user proxies using the repository."""
    with database.get_session() as session:
        user_repository = UserRepository(session)
        user, created = user_repository.get_or_create_user_by_telegram_data(
            session=session,
            telegram_user_id=user_id,
            username=username,
            chat_id=chat_id,
            joined_at=datetime.now(),
        )
        if user is None:
            # Handle the case where user creation/retrieval fails 
            return [] 

        #proxy_repo = ProxyRepository(session)
        #return proxy_repo.get_user_proxies(user.id)
        connection_repo = ConnectionRepository(session)
        return connection_repo.get_user_connections(user.id)
    
    
def get_user_connections(database, username, chat_id, user_id):
    """Retrieves user connections using the repository."""
    with database.get_session() as session:
        user_repository = UserRepository(session)
        user, created = user_repository.get_or_create_user_by_telegram_data(
            session=session,
            telegram_user_id=user_id,
            username=username,
            chat_id=chat_id,
            joined_at=datetime.now(),
        )
        if user is None:
            # Handle the case where user creation/retrieval fails
            return []

        connection_repo = ConnectionRepository(session)  # Use ConnectionRepository
        return connection_repo.get_user_connections(user.id)
    