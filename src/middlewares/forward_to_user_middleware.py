import logging
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, ContentTypes
from src.bot.config import ADMIN_CHAT_ID
from aiogram import Bot

# Dictionary to map forwarded admin messages to original user messages
forwarded_message_mapping = {}

class ForwardToUserMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: Message, data: dict):
        if message.chat.id == ADMIN_CHAT_ID and message.reply_to_message:
            bot = Bot.get_current()
            original_message = forwarded_message_mapping.get(message.reply_to_message.message_id)
            if original_message:
                original_user_chat_id = original_message.chat.id
                try:
                    forward_fn_map = {
                        'text': bot.send_message,
                        'photo': bot.send_photo,
                        'document': bot.send_document,
                        'sticker': bot.send_sticker,
                        'audio': bot.send_audio,
                        'video': bot.send_video,
                        'voice': bot.send_voice,
                        'contact': bot.send_contact,
                        'location': bot.send_location,
                        'venue': bot.send_venue
                    }

                    content_type = message.content_type
                    forward_fn = forward_fn_map.get(content_type, bot.send_message)

                    if content_type in ['photo', 'document', 'audio', 'video', 'voice']:
                        content = getattr(message, content_type)[-1].file_id
                    elif content_type in ['contact', 'location', 'venue']:
                        content = message.get_args()
                    else:
                        content = message.text or "Unsupported content type."

                    if content_type == 'text':
                        await forward_fn(chat_id=original_user_chat_id, text=content)
                    else:
                        await forward_fn(chat_id=original_user_chat_id, **content, caption=message.caption)

                    await message.reply("Your reply has been sent to the user.")
                except Exception as e:
                    logging.exception(f"Error sending reply to user: {e}")
                    await message.reply("Failed to send the reply to the user.")
            else:
                await message.reply("The original user message could not be found.")
