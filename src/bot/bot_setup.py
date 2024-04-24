from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from .config import *


# Create a bot instance and connect to the API
bot = Bot(TG_BOT_TOKEN)

# Create a Dispatcher instance and attach the bot to it
dp = Dispatcher(bot, storage=MemoryStorage())

# Create a middleware to handle the LifetimeController
lifetime_controller_middleware = LifetimeControllerMiddleware()

# Register the middleware with the dispatcher
dp.middleware.setup(lifetime_controller_middleware)

client_message_mapping = {}