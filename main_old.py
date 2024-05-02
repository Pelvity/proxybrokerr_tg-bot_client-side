# main.py
from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from src.bot.config import *
from src.classes import *
from src.utils.helpers import *
from src.bot.bot_setup import *
from src.bot.startup_shutdown import *
from src.utils.keyboards import *

# Create and configure the custom logger
custom_logger = create_custom_logger()

dp.middleware.setup(LoggingMiddleware(custom_logger))

# Register the command handler and attach the keyboard to the message
@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Hello! I am Proxy Helper", reply_markup=keyboard_main)

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def forward_client_message(message: types.Message):
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
    elif message.text == "📜 Agreement":
        await bot.send_message(chat_id=message.chat.id, text=agreement_text(), reply_markup=keyboard_main)
    if message.chat.id == int(ADMIN_CHAT_ID) and message.reply_to_message:
        await send_reply_to_client(message)
    else:
        await forward_message_to_admin(message)

@dp.message_handler(lambda message: message.chat.id == ADMIN_CHAT_ID and message.reply_to_message, content_types=types.ContentTypes.ANY)
async def handle_admin_reply(message: types.Message):
    await send_reply_to_client(message)
    
def agreement_text():
    english_text = """
## Proxy Rental Agreement

By renting a mobile proxy from our service in Poland, you agree to the following terms and conditions:

1. The proxy is provided for legitimate use only and must not be used for any illegal activities.
2. The rental period and pricing will be as agreed upon during the purchase process.
3. We do not guarantee 100% uptime of the proxy, but will strive to maintain high availability.
4. In case of any issues with the proxy, please contact our support team for assistance.
5. Refunds will be considered on a case-by-case basis and are not guaranteed.

Thank you for choosing our mobile proxy rental service in Poland!
"""

    russian_text = """
## Соглашение об аренде прокси

Арендуя мобильный прокси у нашего сервиса в Польше, вы соглашаетесь со следующими условиями:

1. Прокси предоставляется только для законного использования и не должен использоваться для каких-либо незаконных действий.
2. Срок аренды и цены будут согласованы в процессе покупки.
3. Мы не гарантируем 100% времени безотказной работы прокси, но будем стремиться поддерживать высокую доступность.
4. В случае возникновения каких-либо проблем с прокси, пожалуйста, обратитесь в нашу службу поддержки за помощью.
5. Возврат средств будет рассматриваться в каждом конкретном случае и не гарантируется.

Благодарим вас за выбор нашего сервиса аренды мобильных прокси в Польше!
"""

    return f"{english_text}\n\n{russian_text}"
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