# src/utils/logging_utils.py

import logging
import pytz
from .custom_logging import WarsawTimeFormatter, CustomLoggingFilter

def create_custom_logger():
    custom_logger = logging.getLogger(__name__)
    custom_logger.setLevel(logging.INFO)
    custom_logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    bold_start = "\033[1m"
    bold_end = "\033[0m"
    
    # Set the desired timezone (e.g., 'Europe/Warsaw')
    timezone = pytz.timezone('Europe/Warsaw')
    
    warsaw_formatter = WarsawTimeFormatter(
        f"%(asctime)s [%(client_ip)s] User: {bold_start}%(client_username)s{bold_end} %(log_message)s Message: %(user_message)s",
        "%d/%b/%Y:%H:%M:%S",
        timezone=timezone
    )

    console_handler.setFormatter(warsaw_formatter)
    custom_logger.addFilter(CustomLoggingFilter())
    custom_logger.addHandler(console_handler)

    return custom_logger

def log_user_interaction(message, custom_logger):
    user_username = message.from_user.username if message.from_user else "Unknown"
    client_ip = str(message.from_user.id) if message.from_user else "Unknown"  # Convert to string
    user_message = message.text or "No text"
    
    chat_type = message.chat.type
    chat_id = message.chat.id
    message_id = message.message_id
    
    extra = {
        "client_ip": client_ip,
        "client_username": user_username,
        "user_message": user_message,
        "log_message": f"Received message [ID:{message_id}] in chat [{chat_type}:{chat_id}]"
    }
    
    logger = logging.LoggerAdapter(custom_logger, extra)
    logger.info(f"->")
