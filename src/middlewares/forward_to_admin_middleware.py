import logging
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types, Bot, Dispatcher
from src.bot.config import ADMIN_CHAT_ID
from src.bot.bot_setup import database
from src.db.repositories.user_repositories import UserRepository
from datetime import datetime
import pytz

# Dictionary to map forwarded admin messages to original user messages
forwarded_message_mapping = {}

class ForwardToAdminMiddleware(BaseMiddleware):
    def __init__(self):
        super(ForwardToAdminMiddleware, self).__init__()

    async def on_post_process_message(self, message: types.Message, results, data: dict):
        await self.update_user_and_forward(message)

    async def update_user_and_forward(self, message: types.Message):
        if message.from_user and message.chat.id != ADMIN_CHAT_ID:
            session = database.Session()
            try:
                user_repository = UserRepository(session)
                user = user_repository.get_or_create_user(message)
                if user:
                    user['last_message_at'] = datetime.now(pytz.utc)
                    session.commit()
                await self.forward_message_to_admin(message)
            except Exception as e:
                session.rollback()
                logging.error(f"Error updating user and forwarding message: {e}")
            finally:
                session.close()

    async def forward_message_to_admin(self, message: types.Message):
        bot = Bot.get_current()
        try:
            # Skip forwarding for messages from admin chat
            if message.chat.id == ADMIN_CHAT_ID:
                return

            client_username = message.from_user.username
            client_chat_id = message.chat.id
            client_name = message.from_user.full_name

            if client_username:
                header_text = f"@{client_username}\nChat ID:{client_chat_id}\nTG:{message.from_id}"
            else:
                header_text = f"{client_name}\nChat ID:{client_chat_id}\nTG:{message.from_id}"

            forwarded_message = None

            if message.text:
                forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{header_text}\n{message.text}")
            elif message.photo:
                photo = message.photo[-1]
                forwarded_message = await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo.file_id, caption=header_text)
            elif message.document:
                forwarded_message = await bot.send_document(chat_id=ADMIN_CHAT_ID, document=message.document.file_id, caption=header_text)
            elif message.sticker:
                forwarded_message = await bot.send_sticker(chat_id=ADMIN_CHAT_ID, sticker=message.sticker.file_id)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            elif message.audio:
                forwarded_message = await bot.send_audio(chat_id=ADMIN_CHAT_ID, audio=message.audio.file_id, caption=header_text)
            elif message.video:
                forwarded_message = await bot.send_video(chat_id=ADMIN_CHAT_ID, video=message.video.file_id, caption=header_text)
            elif message.voice:
                forwarded_message = await bot.send_voice(chat_id=ADMIN_CHAT_ID, voice=message.voice.file_id, caption=header_text)
            elif message.contact:
                forwarded_message = await bot.send_contact(chat_id=ADMIN_CHAT_ID, phone_number=message.contact.phone_number, first_name=message.contact.first_name, last_name=message.contact.last_name)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            elif message.location:
                forwarded_message = await bot.send_location(chat_id=ADMIN_CHAT_ID, latitude=message.location.latitude, longitude=message.location.longitude)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            elif message.venue:
                forwarded_message = await bot.send_venue(chat_id=ADMIN_CHAT_ID, latitude=message.venue.location.latitude, longitude=message.venue.location.longitude, title=message.venue.title, address=message.venue.address)
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=header_text)
            else:
                forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"{header_text}\nUnsupported content type.")

            # Track the forwarded message
            if forwarded_message:
                forwarded_message_mapping[forwarded_message.message_id] = message

        except Exception as e:
            logging.exception(f"Error in ForwardToAdminMiddleware: {e}")