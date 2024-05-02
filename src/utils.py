import logging
from datetime import datetime
from typing import List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests


from .bot_setup import *
from .custom_logging import WarsawTimeFormatter, CustomLoggingFilter


def create_custom_logger():
    custom_logger = logging.getLogger(__name__)
    custom_logger.setLevel(logging.INFO)
    custom_logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    bold_start = "\033[1m"
    bold_end = "\033[0m"
    
    warsaw_formatter = WarsawTimeFormatter(
        f"%(asctime)s [%(client_ip)s] User: {bold_start}%(client_username)s{bold_end} %(message)s Message: %(user_message)s",
        "%d/%b/%Y:%H:%M:%S"
    )

    console_handler.setFormatter(warsaw_formatter)
    custom_logger.addFilter(CustomLoggingFilter())
    custom_logger.addHandler(console_handler)

    return custom_logger

def log_user_interaction(message, custom_logger):
    user_username = message.from_user.username
    client_ip = message.from_user.id  # Assuming this is the client IP
    user_message = message.text or "No text"
    extra = {"client_ip": client_ip, "client_username": user_username, "user_message": user_message}
    logger = logging.LoggerAdapter(custom_logger, extra)
    logger.info(f"->")


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


async def send_proxies(chat_id: int, proxies: List[Tuple]):
    buttons = [
        InlineKeyboardButton(
            text=f"{name} | {date} | {days_left} days {hours_left} hours left",
            callback_data=f"proxy_{connection_id}_{i + 1}",
        )
        for i, (name, date, days_left, hours_left, connection_id) in enumerate(proxies)
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
