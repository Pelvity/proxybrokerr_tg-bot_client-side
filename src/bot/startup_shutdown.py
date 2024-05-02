import logging
from .bot_setup import bot, dp, ADMIN_CHAT_ID, WEBHOOK_URL, PORT
from aiogram import Dispatcher
from src.utils.background_tasks import sync_proxy_connections
import asyncio

async def on_startup(dp):
    if WEBHOOK_URL:  # If WEBHOOK_URL is set, use webhook mode
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text='Bot has been started with WEBHOOK')
        logging.info("Bot has been started with WEBHOOK")
        await bot.set_webhook(url=WEBHOOK_URL)
    else:  # If WEBHOOK_URL is not set, use long polling mode
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text='Bot has been started (long polling)')
    asyncio.create_task(sync_proxy_connections())

async def on_shutdown(dp):
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text='Bot has been stopped')
