import logging
import pytz
from aiogram import types
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

def log_user_interaction(message: types.Message, custom_logger):
    user_username = message.from_user.username if message.from_user else "Unknown"
    client_ip = str(message.from_user.id) if message.from_user else "Unknown"
    chat_type = message.chat.type
    chat_id = message.chat.id
    message_id = message.message_id
    
    # Determine message content type and extract details
    if message.text:
        user_message = f"Text: {message.text}"
    elif message.photo:
        user_message = "Photo received"
    elif message.audio:
        user_message = f"Audio received: {message.audio.file_id}"
    elif message.document:
        user_message = f"Document received: {message.document.file_name}"
    elif message.video:
        user_message = f"Video received: {message.video.file_id}"
    elif message.voice:
        user_message = f"Voice message received: {message.voice.file_id}"
    elif message.sticker:
        user_message = f"Sticker received: {message.sticker.emoji}"
    elif message.contact:
        user_message = f"Contact shared: {message.contact.phone_number} - {message.contact.first_name}"
    elif message.location:
        user_message = f"Location shared: Latitude {message.location.latitude}, Longitude {message.location.longitude}"
    elif message.venue:
        user_message = f"Venue shared: {message.venue.title}, Address: {message.venue.address}"
    else:
        user_message = "Unknown content type"

    extra = {
        "client_ip": client_ip,
        "client_username": user_username,
        "user_message": user_message,
        "log_message": f"Received message [ID:{message_id}] in chat [{chat_type}:{chat_id}]"
    }
    
    logger = logging.LoggerAdapter(custom_logger, extra)
    logger.info("Message: ->")

