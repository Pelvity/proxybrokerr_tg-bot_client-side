from datetime import datetime
import logging
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, ContentTypes
from src.bot.config import ADMIN_CHAT_ID
from aiogram import Bot
from src.db.repositories.user_repositories import UserRepository
from sqlalchemy.orm import Session
from src.db.database import get_db_session
import pytz

# Dictionary to map forwarded admin messages to original user messages
forwarded_message_mapping = {}

class ForwardToAdminMiddleware(BaseMiddleware):
    def __init__(self):
        super(ForwardToAdminMiddleware, self).__init__()
        self.db_session = get_db_session()
        self.user_repository = UserRepository(self.db_session)

    async def on_post_process_message(self, message: Message, results, data: dict):
        # Update last_message_at for the user
        if message.from_user and message.chat.id != ADMIN_CHAT_ID:
            try:
                user = self.user_repository.get_user_by_telegram_user_id(message.from_user.id)
                if user:
                    user.last_message_at = datetime.now(pytz.utc)
                    self.db_session.commit()
            except Exception as e:
                logging.exception(f"Error updating last_message_at: {e}")
        # Skip messages that are replies from the admin
        if message.chat.id == ADMIN_CHAT_ID and message.reply_to_message:
            return

        if message.chat.id != ADMIN_CHAT_ID:
            bot = Bot.get_current()
            try:
                client_username = message.from_user.username
                client_chat_id = message.chat.id
                client_name = message.from_user.full_name

                if client_username:
                    header_text = f"@{client_username} (Chat ID: {client_chat_id})"
                else:
                    header_text = f"{client_name} (Chat ID: {client_chat_id})"

                forwarded_message = None

                if message.content_type == 'text':
                    forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{header_text}\n{message.text}")
                elif message.content_type == 'photo':
                    photo = message.photo[-1]
                    forwarded_message = await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo.file_id, caption=header_text)
                elif message.content_type == 'document':
                    forwarded_message = await bot.send_document(chat_id=ADMIN_CHAT_ID, document=message.document.file_id, caption=header_text)
                elif message.content_type == 'sticker':
                    forwarded_message = await bot.send_sticker(chat_id=ADMIN_CHAT_ID, sticker=message.sticker.file_id)
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
                elif message.content_type == 'audio':
                    forwarded_message = await bot.send_audio(chat_id=ADMIN_CHAT_ID, audio=message.audio.file_id, caption=header_text)
                elif message.content_type == 'video':
                    forwarded_message = await bot.send_video(chat_id=ADMIN_CHAT_ID, video=message.video.file_id, caption=header_text)
                elif message.content_type == 'voice':
                    forwarded_message = await bot.send_voice(chat_id=ADMIN_CHAT_ID, voice=message.voice.file_id, caption=header_text)
                elif message.content_type == 'contact':
                    forwarded_message = await bot.send_contact(chat_id=ADMIN_CHAT_ID, phone_number=message.contact.phone_number, first_name=message.contact.first_name, last_name=message.contact.last_name)
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
                elif message.content_type == 'location':
                    forwarded_message = await bot.send_location(chat_id=ADMIN_CHAT_ID, latitude=message.location.latitude, longitude=message.location.longitude)
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
                elif message.content_type == 'venue':
                    forwarded_message = await bot.send_venue(chat_id=ADMIN_CHAT_ID, latitude=message.venue.location.latitude, longitude=message.venue.location.longitude, title=message.venue.title, address=message.venue.address)
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
                else:
                    forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{header_text}\nUnsupported content type.")

                # Track the forwarded message
                forwarded_message_mapping[forwarded_message.message_id] = message

            except Exception as e:
                logging.exception(f"Error forwarding message to admin: {e}")
                
    async def close(self):
        if self.db_session:
            self.db_session.close()
