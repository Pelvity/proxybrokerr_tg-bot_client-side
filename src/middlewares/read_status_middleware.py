# import logging
# from aiogram.dispatcher.middlewares import BaseMiddleware
# from aiogram.types import Message, ContentTypes
# from aiogram import Bot, types
# from src.bot.config import ADMIN_CHAT_ID
# from src.bot.bot_setup import aws_rds_service
# from src.db.repositories.message_repositories import MessageRepository

# class ReadStatusMiddleware(BaseMiddleware):
#     def __init__(self):
#         super().__init__()
#         self.read_emoji = "👁️"  # Eye emoji to indicate "seen"

#     async def on_pre_process_message(self, message: types.Message, data: dict):
#         if message.chat.id != ADMIN_CHAT_ID:
#             bot = Bot.get_current()
#             try:
#                 with aws_rds_service.get_session() as session:
#                     message_repo = MessageRepository(session)
#                     unread_admin_messages = message_repo.get_unread_admin_messages(message.chat.id)
                    
#                     for admin_message in unread_admin_messages:
#                         # Mark the message as read in the database
#                         message_repo.mark_message_as_read(admin_message.id)
                        
#                         # Add "read" reaction to the admin's message
#                         await bot.set_message_reaction(
#                             chat_id=ADMIN_CHAT_ID,
#                             message_id=admin_message.admin_message_id,
#                             reaction=[types.ReactionTypeEmoji(emoji=self.read_emoji)],
#                             is_big=False
#                         )
                        
#             except Exception as e:
#                 logging.exception(f"Error updating read status: {e}")

#     async def on_post_process_message(self, message: types.Message, results, data: dict):
#         if message.chat.id == ADMIN_CHAT_ID and message.reply_to_message:
#             # This is an admin replying to a user message
#             try:
#                 with aws_rds_service.get_session() as session:
#                     message_repo = MessageRepository(session)
#                     message_repo.save_admin_message(
#                         user_id=message.reply_to_message.forward_from.id,
#                         admin_message_id=message.message_id
#                     )
#             except Exception as e:
#                 logging.exception(f"Error saving admin message: {e}")