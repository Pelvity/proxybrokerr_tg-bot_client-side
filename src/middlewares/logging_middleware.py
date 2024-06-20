# src/middlewares/logging_middleware.py

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types

from src.utils.logging_utils import log_user_interaction

class LoggingMiddleware(BaseMiddleware):

    def __init__(self, custom_logger):
        self.custom_logger = custom_logger
        super().__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        self.custom_logger.info(f"Pre-processing message from user {message.from_user.id}")
        log_user_interaction(message, self.custom_logger)
