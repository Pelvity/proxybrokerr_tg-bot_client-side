from aiogram import executor
from src.bot.config import *
from src.bot.bot_setup import *
from src.bot.startup_shutdown import *

#from src.bot.handlers.start_handlers import *
from src.bot.handlers.client_handlers import *
from src.bot.handlers.admin_handlers import *
from src.bot.handlers.common_handlers import *
from src.utils.logging_utils import create_custom_logger
from src.middlewares.logging_middleware import LoggingMiddleware
from src.middlewares.forward_to_admin_middleware import ForwardToAdminMiddleware

# Create and configure the custom logger
custom_logger = create_custom_logger()

# Set up logging middleware
dp.middleware.setup(LoggingMiddleware(custom_logger))
dp.middleware.setup(ForwardToAdminMiddleware())

if __name__ == "__main__":
    try:
        if WEBHOOK_URL:
            executor.start_webhook(
                dispatcher=dp,
                webhook_path="/",
                on_startup=on_startup,
                on_shutdown=on_shutdown,
                skip_updates=False,
                host="0.0.0.0",
                port=int(PORT)
            )
        else:
            print("long polling mode")
            executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=False)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
