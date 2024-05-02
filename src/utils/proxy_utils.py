# src/utils/proxy_utils.py

from datetime import datetime
from typing import List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from src.bot.bot_setup import bot
from src.bot.config import BASE_API_URL, AUTH_HEADER
from src.bot.models.proxy_models import Proxy
from src.db.models.db_models import *

def parse_proxy_names(proxy_names: List[str], user_connections: List[dict], now: datetime) -> List[Tuple]:
    parsed = [
        (
            name_desc.split(" - ")[0],
            name_desc.split(" - ")[1],
            (datetime.strptime(name_desc.split(" - ")[1], "%d/%m/%Y") - now).days,
            (datetime.strptime(name_desc.split(" - ")[1], "%d/%m/%Y") - now).seconds // 3600,
            conn["id"],
        )
        for name_desc, conn in zip(proxy_names, user_connections)
    ]
    parsed.sort(key=lambda x: x[1])
    return parsed

async def send_proxies(chat_id: int, proxies: List[Proxy]):
    buttons = [
        InlineKeyboardButton(
            text=f"{proxy.name} | {proxy.expiration_date.strftime('%d/%m/%Y')} | {proxy.days_left} days {proxy.hours_left} hours left",
            callback_data=f"proxy_{proxy.service_name}_{proxy.authToken}_{i + 1}",
        )
        for i, proxy in enumerate(proxies)
    ]
    keyboard = InlineKeyboardMarkup(row_width=1).add(*buttons)
    await bot.send_message(chat_id=chat_id, text="Proxy:", reply_markup=keyboard)

async def get_connections():
    response = requests.get(f"{BASE_API_URL}/connections", headers=AUTH_HEADER)
    return response.json()["result"]

async def get_connection_info(connection_id):
    response = requests.get(f"{BASE_API_URL}/connections/{connection_id}", headers=AUTH_HEADER)
    return response.json()["result"]

async def get_proxies(connection_id):
    response = requests.get(f"{BASE_API_URL}/connections/{connection_id}/proxies", headers=AUTH_HEADER)
    return response.json()["result"]

# src/utils/proxy_utils.py

# src/utils/proxy_utils.py
from src.db.models.db_models import DBProxy

# This dictionary will store the proxy selections for each user.
# The keys are user_ids and the values are sets of selected proxy_ids.
user_selections = {}

def toggle_proxy_selection(user_id, proxy_id):
    # Retrieve the current selections for the user, or initialize with an empty set
    current_selections = user_selections.get(user_id, set())
    
    # Toggle the proxy_id in the set
    if proxy_id in current_selections:
        current_selections.remove(proxy_id)
    else:
        current_selections.add(proxy_id)
    
    # Update the user_selections dictionary
    user_selections[user_id] = current_selections
    return current_selections

def get_all_proxies():
    # Fetch all proxies from the DBProxy model
    return list(DBProxy.select())

def get_selected_proxies(user_id):
    # Return the set of selected proxy IDs for the user
    return user_selections.get(user_id, set())

def process_payment_for_proxies(user_id, proxy_ids):
    # Process the payment for the selected proxies
    for proxy_id in proxy_ids:
        proxy = DBProxy.get(DBProxy.id == proxy_id)
        # Example: Update proxy status, payment records, etc.
        proxy.active = True
        proxy.save()

def get_user_proxies(username, chat_id, user_id):
    # Sync user data (id and chat_id) using the provided username
    user, created = User.get_or_create(
        username=username,
        defaults={
            'chat_id': chat_id,
            'id': user_id,
            'joined_at': datetime.now(),
            'last_message_at': datetime.now(),
            'is_active': True
        }
    )

    if not created:
        # Update the user's chat_id and last_message_at if the user already exists
        user.chat_id = chat_id
        user.last_message_at = datetime.now()
        user.save()

    # Retrieve the list of proxies that belong to the user and are due for payment or have expired
    proxies = list(DBProxy.select().where(
        (DBProxy.user == user)
    ))

    return proxies
