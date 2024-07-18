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
        await self.forward_message_to_admin(message)

    async def forward_message_to_admin(self, message: types.Message):
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

# async def check_for_missed_updates():
#     bot = Bot.get_current()
#     dp = Dispatcher(bot)

#     try:
#         updates = await bot.get_updates()
#         for update in updates:
#             if update.message:
#                 # Manually process each message as if it was just received
#                 message = update.message
#                 await dp.process_update(update)
#                 forward_middleware = dp.middleware._middlewares[0]  # Get the instance of ForwardToAdminMiddleware
#                 if isinstance(forward_middleware, ForwardToAdminMiddleware):
#                     await forward_middleware.forward_message_to_admin(message)
#             # Acknowledge the update to remove it from the pending updates queue
#             await bot.get_updates(offset=update.update_id + 1)
#     except Exception as e:
#         logging.exception(f"Error checking for missed updates: {e}")
