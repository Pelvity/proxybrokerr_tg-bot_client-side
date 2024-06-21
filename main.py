import logging
logging.info("Main.py")
from aiogram import executor
from src.bot.config import *
from src.bot.bot_setup import *
from src.bot.startup_shutdown import *
from src.bot.handlers.client_handlers import *
from src.bot.handlers.admin_handlers import *
from src.bot.handlers.common_handlers import *
from src.utils.logging_utils import create_custom_logger
from src.middlewares.logging_middleware import LoggingMiddleware
from src.middlewares.forward_to_admin_middleware import ForwardToAdminMiddleware

logging.info("Main.py")

# Create and configure the custom logger
custom_logger = create_custom_logger()
logging.basicConfig(level=logging.INFO)

logging.info("custom logger done")

# Set up logging middleware
dp.middleware.setup(LoggingMiddleware(custom_logger))
dp.middleware.setup(ForwardToAdminMiddleware())

if __name__ == "__main__":
    try:
        logging.info("Bot is starting...")
        logging.info(f"TOKEN: {TG_BOT_TOKEN}")
        logging.info(f"ADMIN_CHAT_ID: {ADMIN_CHAT_ID}")
        logging.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
        logging.info(f"PORT: {PORT}")

        if WEBHOOK_URL:
            logging.info("Starting in webhook mode...")
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
            logging.info("Starting in long polling mode...")
            executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=False)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
