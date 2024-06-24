import logging
logging.info("bot_setup.py")
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from src.db.azure_db import AzureSQLService
from src.db.aws_db import AWSRDSService
from .config import TG_BOT_TOKEN, DATABASE_TYPE

# Create bot, dispatcher, and middleware
bot = Bot(TG_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
lifetime_controller_middleware = LifetimeControllerMiddleware()
dp.middleware.setup(lifetime_controller_middleware)

# Initialize the database based on the DATABASE_TYPE
if DATABASE_TYPE == "azure":
    database = AzureSQLService()
elif DATABASE_TYPE == "aws":
    database = AWSRDSService()
else:
    raise ValueError("Unsupported DATABASE_TYPE. Please set it to either 'azure' or 'aws'.")

database.create_tables()

# ... rest of your bot setup (import handlers, etc.) ...

client_message_mapping = {}
