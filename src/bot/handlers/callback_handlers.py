from aiogram import types
from src.bot.bot_setup import bot, dp
from src.utils.proxy_utils import send_proxies
from src.services.iproxyService import IProxyManager
from src.services.localtonetService import LocaltonetManager
from src.bot.config import IPROXY_API_KEY, LOCALTONET_API_KEY, PM_BINANCE_PAYID, PM_BINANCE_USDT_TRC20, PM_PEKAOBANK, PM_PRIVATBANK

iproxy_manager = IProxyManager(IPROXY_API_KEY)
localtonet_manager = LocaltonetManager(LOCALTONET_API_KEY)

@dp.callback_query_handler(lambda query: query.data == "my_proxy")
async def my_proxy_callback(query: types.CallbackQuery):
    iproxy_connections = await iproxy_manager.getAllProxies()
    localtonet_connections = await localtonet_manager.getAllProxies()
    all_connections = iproxy_connections + localtonet_connections

    user_username = query.from_user.username
    user_connections = [conn for conn in all_connections if conn.user == user_username]

    if not user_connections:
        await bot.send_message(chat_id=query.message.chat.id, text="You have no proxies\nBuy it directly:\nhttps://t.me/proxybrokerr")
    else:
        await send_proxies(query.message.chat.id, user_connections)
    await query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('proxy'))
async def process_proxy_selection(callback_query: types.CallbackQuery):
    _, service_name, connection_id, button_index = callback_query.data.split('_')
    
    if service_name == 'ipr':
        proxies = await iproxy_manager.getConnectionsOfProxy(connection_id)
    elif service_name == 'ltn':
        proxies = await localtonet_manager.getConnectionsOfProxy(connection_id)
    else:
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Invalid service name.")
        return

    proxy_info = "\n".join([f"Connection: `{proxy.type}://{proxy.host}:{proxy.port}:{proxy.login}:{proxy.password}`\n\nType:  `{proxy.type}`\nIP:    `{proxy.host}`\nPort:  `{proxy.port}`\nLogin: `{proxy.login}`\nPass:  `{proxy.password}`\n" for proxy in proxies])
    await bot.send_message(chat_id=callback_query.message.chat.id, text=proxy_info, parse_mode='Markdown')

@dp.callback_query_handler(lambda query: query.data.startswith("info_"))
async def handle_info_callback_query(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    chat_id = callback_query.message.chat.id

    if callback_data == "info_proxy_details":
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

    elif callback_data == "info_prices":
        prices = """
💰 *Price*

        • 1 day: .......... *3$*
        • 7 days: ...... *15$*
        • 30 days: .. *50$*

*‼️ -10% FIRST RENT ‼️*
        """
        await bot.send_message(chat_id=chat_id, text=prices, parse_mode="Markdown")

    elif callback_data == "info_payment_methods":
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

    elif callback_data == "info_discounts":
        discounts = """
🤝 *Discounts*

        ❤️ -10% fist rent
        ❤️ long term coop discounts
        """
        await bot.send_message(chat_id=chat_id, text=discounts, parse_mode="Markdown")

    elif callback_data == "info_features":
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