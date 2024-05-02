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
    iproxy_connections = await iproxy_manager.getConnections()
    localtonet_connections = await localtonet_manager.getConnections()
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
        proxies = await iproxy_manager.getProxiesforConnection(connection_id)
    elif service_name == 'ltn':
        proxies = await localtonet_manager.getProxiesforConnection(connection_id)
    else:
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Invalid service name.")
        return

    proxy_info = "\n".join([f"Connection: `{proxy.type}://{proxy.ip}:{proxy.port}:{proxy.login}:{proxy.password}`\n\nType:  `{proxy.type}`\nIP:    `{proxy.ip}`\nPort:  `{proxy.port}`\nLogin: `{proxy.login}`\nPass:  `{proxy.password}`\n" for proxy in proxies])
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

from src.services.payment_service import process_payment


""" PAYMENT """
# src/bot/handlers/callback_handlers.py
from aiogram import types, Dispatcher
from src.services.payment_service import process_payment, confirm_payment

async def handle_pay_now(callback_query: types.CallbackQuery):
    # Parse the callback data to extract user_id, proxy_id, and payment_period
    _, user_id_str, proxy_id_str, payment_period = callback_query.data.split(':')
    user_id = int(user_id_str)
    proxy_id = int(proxy_id_str)

    # Call the process_payment function with the extracted data
    await process_payment(user_id, proxy_id, payment_period)
    await callback_query.answer("Payment processed, awaiting confirmation.")

async def handle_confirm_payment(callback_query: types.CallbackQuery):
    # Extract payment_id from the callback data
    _, payment_id_str = callback_query.data.split(':')
    payment_id = int(payment_id_str)

    # Call the confirm_payment function with the extracted payment_id
    await confirm_payment(payment_id)
    await callback_query.answer("Payment confirmed.")

# Assuming this is in your callback_handlers.py or a similar file

from aiogram import types
from src.utils.proxy_utils import toggle_proxy_selection, get_all_proxies, get_selected_proxies, process_payment_for_proxies
from src.utils.keyboards import payment_keyboard

async def handle_toggle_proxy(callback_query: types.CallbackQuery):
    proxy_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id
    selected_proxies = toggle_proxy_selection(user_id, proxy_id)
    proxies = get_all_proxies()
    new_keyboard = payment_keyboard(proxies, selected_proxies)
    await callback_query.message.edit_reply_markup(reply_markup=new_keyboard)
    await callback_query.answer()

async def handle_confirm_payment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    selected_proxies = get_selected_proxies(user_id)
    process_payment_for_proxies(user_id, selected_proxies)
    await callback_query.message.edit_text("Payment confirmed for selected proxies.")
    await callback_query.answer()

# In your callback handlers file
from src.utils.helpers import get_user_from_callback, get_proxy_from_callback, get_payment_period_from_callback, get_payment_id_from_callback

async def handle_payment_callback(callback_query: types.CallbackQuery):
    user = await get_user_from_callback(callback_query)
    proxy = await get_proxy_from_callback(callback_query)
    payment_period = await get_payment_period_from_callback(callback_query)
    # Process the payment logic here

def register_payment_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(handle_pay_now, lambda c: c.data.startswith('pay_proxy'))
    dp.register_callback_query_handler(handle_confirm_payment, lambda c: c.data.startswith('confirm_payment'))
    dp.register_callback_query_handler(handle_toggle_proxy, lambda c: c.data.startswith('toggle_proxy'))
    dp.register_callback_query_handler(handle_confirm_payment, lambda c: c.data == 'confirm_payment')
