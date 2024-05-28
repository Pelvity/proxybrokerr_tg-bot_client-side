from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from src.db.azure_db import AzureSQLService 
from .config import TG_BOT_TOKEN

# Create bot, dispatcher, and middleware
bot = Bot(TG_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
lifetime_controller_middleware = LifetimeControllerMiddleware()
dp.middleware.setup(lifetime_controller_middleware)

# Initialize the database
database = AzureSQLService() 
database.create_tables() 

# ... rest of your bot setup (import handlers, etc.) ... 

client_message_mapping = {} 