import logging
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, ContentTypes
from src.bot.config import ADMIN_CHAT_ID
from aiogram import Bot
from src.bot.bot_setup import database
from src.db.repositories.user_repositories import UserRepository
from datetime import datetime
import pytz

# Dictionary to map forwarded admin messages to original user messages
forwarded_message_mapping = {}

class ForwardToAdminMiddleware(BaseMiddleware):
    def __init__(self):
        super(ForwardToAdminMiddleware, self).__init__()

    async def on_post_process_message(self, message: Message, results, data: dict):
        bot = Bot.get_current()
        try:
            # Update last_message_at for the user
            if message.from_user and message.chat.id != ADMIN_CHAT_ID:
                with database.get_session() as session:
                    user_repository = UserRepository(session)
                    user = user_repository.get_user_by_telegram_user_id(message.from_user.id)
                    if user:
                        user.last_message_at = datetime.now(pytz.utc)
                        session.commit()

            # Skip forwarding for messages from admin chat
            if message.chat.id == ADMIN_CHAT_ID:
                return

            client_username = message.from_user.username
            client_chat_id = message.chat.id
            client_name = message.from_user.full_name

            if client_username:
                header_text = f"@{client_username} (Chat ID: {client_chat_id})"
            else:
                header_text = f"{client_name} (Chat ID: {client_chat_id})"

            forwarded_message = None

            if message.content_type == ContentTypes.TEXT:
                forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{header_text}\n{message.text}")
            elif message.content_type == ContentTypes.PHOTO:
                photo = message.photo[-1]
                forwarded_message = await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo.file_id, caption=header_text)
            elif message.content_type == ContentTypes.DOCUMENT:
                forwarded_message = await bot.send_document(chat_id=ADMIN_CHAT_ID, document=message.document.file_id, caption=header_text)
            elif message.content_type == ContentTypes.STICKER:
                forwarded_message = await bot.send_sticker(chat_id=ADMIN_CHAT_ID, sticker=message.sticker.file_id)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            elif message.content_type == ContentTypes.AUDIO:
                forwarded_message = await bot.send_audio(chat_id=ADMIN_CHAT_ID, audio=message.audio.file_id, caption=header_text)
            elif message.content_type == ContentTypes.VIDEO:
                forwarded_message = await bot.send_video(chat_id=ADMIN_CHAT_ID, video=message.video.file_id, caption=header_text)
            elif message.content_type == ContentTypes.VOICE:
                forwarded_message = await bot.send_voice(chat_id=ADMIN_CHAT_ID, voice=message.voice.file_id, caption=header_text)
            elif message.content_type == ContentTypes.CONTACT:
                forwarded_message = await bot.send_contact(chat_id=ADMIN_CHAT_ID, phone_number=message.contact.phone_number, first_name=message.contact.first_name, last_name=message.contact.last_name)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            elif message.content_type == ContentTypes.LOCATION:
                forwarded_message = await bot.send_location(chat_id=ADMIN_CHAT_ID, latitude=message.location.latitude, longitude=message.location.longitude)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            elif message.content_type == ContentTypes.VENUE:
                forwarded_message = await bot.send_venue(chat_id=ADMIN_CHAT_ID, latitude=message.venue.location.latitude, longitude=message.venue.location.longitude, title=message.venue.title, address=message.venue.address)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            else:
                forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{header_text}\nUnsupported content type.")

            # Track the forwarded message
            if forwarded_message:
                forwarded_message_mapping[forwarded_message.message_id] = message

        except Exception as e:
            logging.exception(f"Error in ForwardToAdminMiddleware: {e}")