import logging
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, ContentTypes
from src.bot.config import ADMIN_CHAT_ID
from aiogram import Bot
from aiogram import types

class ReadStatusMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.chat.id != ADMIN_CHAT_ID:
            bot = Bot.get_current()
            for msg_id, read_status in admin_reply_read_status.items():
                if not read_status:
                    try:
                        # Mark the message as read
                        admin_reply_read_status[msg_id] = True
                        
                        # Send read status to admin
                        await bot.send_message(
                            chat_id=ADMIN_CHAT_ID,
                            text=f"Message (ID: {msg_id}) has been read by the user."
                        )
                    except Exception as e:
                        logging.exception(f"Error updating read status: {e}")

async def check_for_missed_updates():
    bot = Bot.get_current()
    dp = Dispatcher(bot)

    try:
        updates = await bot.get_updates()
        for update in updates:
            if update.message:
                # Manually process each message as if it was just received
                message = update.message
                await dp.process_update(update)
                forward_middleware = dp.middleware._middlewares[0]  # Get the instance of ForwardToAdminMiddleware
                if isinstance(forward_middleware, ForwardToAdminMiddleware):
                    await forward_middleware.forward_message_to_admin(message)
            # Acknowledge the update to remove it from the pending updates queue
            await bot.get_updates(offset=update.update_id + 1)
    except Exception as e:
        logging.exception(f"Error checking for missed updates: {e}")
