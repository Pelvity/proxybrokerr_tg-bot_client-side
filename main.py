from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from src.config import *
from src.classes import *
from src.utils import *
from src.bot_setup import *
from src.startup_shutdown import *
from src.keyboards import *

# Create and configure the custom logger
custom_logger = create_custom_logger()

dp.middleware.setup(LoggingMiddleware(custom_logger))

# Register the command handler and attach the keyboard to the message


@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Hello! I am Proxy Helper", reply_markup=keyboard_main)

@dp.message_handler()
async def kb_answer(message: types.Message):
    if message.text == "🌐 My Proxy":
        now = datetime.now()
        result = await get_connections()

        user_username = message.from_user.username
        user_connections = [conn for conn in result if conn["description"].lstrip('@') == user_username]
        connection_names = [conn["name"] for conn in user_connections]

        if not connection_names:
            await bot.send_message(chat_id=message.chat.id, text="You have no proxies\nBuy it directly:\nhttps://t.me/proxybrokerr")
        else:
            proxies = parse_proxy_names(connection_names, user_connections, now)
            message.connection_id = proxies[0][4]  # Save the first connection_id in the message object for later use
            await send_proxies(message.chat.id, proxies)
    elif message.text == "ℹ️ Info":
        await bot.send_message(chat_id=message.chat.id, text="Select an option:", reply_markup=info_keyboard())
    elif message.text == "💬 Support":
        await bot.send_message(chat_id=message.chat.id, text="https://t.me/proxybrokerr", reply_markup=keyboard_main)
    else:
        await message.reply(f"Your message is: {message.text}")

#!PROXY INFO MENU
@dp.callback_query_handler(lambda c: c.data.startswith('proxy'))
async def process_proxy_selection(callback_query: types.CallbackQuery):
    _, connection_id, button_index = callback_query.data.split('_')
    proxies = await get_proxies(connection_id)
    connection = await get_connection_info(connection_id)
    proxy_info = "\n".join([f"Connection: `{proxy['type']}://{proxy['ip']}:{proxy['port']}:{proxy['login']}:{proxy['password']}`\n\nType:  `{proxy['type']}`\nIP:    `{proxy['ip']}`\nPort:  `{proxy['port']}`\nLogin: `{proxy['login']}`\nPass:  `{proxy['password']}`\nChange IP URL: `{connection['changeIpUrl']}`\n" for proxy in proxies])
    await bot.send_message(chat_id=callback_query.message.chat.id, text=proxy_info, parse_mode='Markdown')

#!INFO MENU
@dp.callback_query_handler()
async def handle_callback_query(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    chat_id = callback_query.message.chat.id

    if callback_data == "main_menu_proxy_details":
        # Handle "🔎 Proxy Details" button action
        proxy_details = """
```
🔎Proxy Details
🇵🇱 GEO:             Poland
📶 Operators:       T-Mobile
🔌 Connection types:http/socks5
🚀 Speed:           up to 40 Mbps
🔄 IP change:       via a link/automatically
🕑 Test:            up to 3 hours
```
"""
        proxy_details_v2 = """
🔎Proxy Details

🇵🇱 GEO:                         *Poland*
📶 Operators:               *T-Mobile*
🔌 Connection types:  *HTTP/SOCKS5/UDP*
🚀 Speed:                      *< 40 Mbps*
🔄 IP change:                *LINK/AUTO*
🕑 Test:                          *up to 3 hours*
🚪 Ports:                      *1 phone = 1 customer*
"""


        await bot.send_message(chat_id=chat_id, text=proxy_details_v2, parse_mode="Markdown")

    elif callback_data == "main_menu_prices":
        # Handle "💰 Prices" button action
        prices = """
💰 *Price*

        • 1 day: .......... *3$*
        • 7 days: ...... *15$*
        • 30 days: .. *50$*

*‼️ -10% FIRST RENT ‼️*
        """
        await bot.send_message(chat_id=chat_id, text=prices, parse_mode="Markdown")

    elif callback_data == "main_menu_payment_methods":
        # Handle "💰 payment_methods" button action
        payment_methods = """
        💳 *Payment Methods*

• Binance PayID
`{PM_BINANCE_PAYID}`

• USDT TRC20
`{PM_BINANCE_USDT_TRC20}`

• Pekao (PL bank)
`{PM_PEKAOBANK}`

• Privat24 (UA bank)
`{PM_PRIVATBANK}`
        """.format(PM_BINANCE_PAYID=PM_BINANCE_PAYID, PM_BINANCE_USDT_TRC20=PM_BINANCE_USDT_TRC20, PM_PEKAOBANK=PM_PEKAOBANK, PM_PRIVATBANK=PM_PRIVATBANK)

        await bot.send_message(chat_id=chat_id, text=payment_methods, parse_mode="Markdown")



    elif callback_data == "main_menu_discounts":
        # Handle "🤝 Discounts" button action
        discounts = """
🤝 *Discounts*

        ❤️ -10% fist rent
        ❤️ long term coop discounts
        """
        await bot.send_message(chat_id=chat_id, text=discounts, parse_mode="Markdown")

    elif callback_data == "main_menu_features":
        # Handle "🔋 Features" button action
        features = """
⚙️ *Features*

🎯 Unique IP capturing function
🛡️ UDP protocol .ovpn config
🔒 Proxy connection without VPN
        """
        await bot.send_message(chat_id=chat_id, text=features, parse_mode="Markdown")

    else:
        await bot.answer_callback_query(callback_query.id, text="Unknown action")

    # Acknowledge the callback query
    await bot.answer_callback_query(callback_query.id)

if __name__ == "__main__":
    from aiogram import executor

    if WEBHOOK_URL:  # If WEBHOOK_URL is set, use webhook mode
        executor.start_webhook(
            dispatcher=dp,
            webhook_path="/",
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=False,
            host="0.0.0.0",
            port=int(PORT)
        )
    else:  # If WEBHOOK_URL is not set, use long polling mode
        print("long polling mode")
        executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=False)