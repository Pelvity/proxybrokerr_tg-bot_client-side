# src/bot/handlers/payment_handlers.py
from aiogram import types
from src.bot.bot_setup import bot, dp
from src.utils.keyboards import payment_keyboard, proxy_payment_keyboard
from src.utils.proxy_utils import toggle_proxy_selection, get_selected_proxies, get_user_proxies
from src.services.payment_service import process_payment, confirm_payment

""" @dp.message_handler(commands=['pay'])
async def handle_pay_command(message: types.Message):
    user_id = message.from_user.id
    proxies = get_user_proxies(user_id)
    selected_proxies = get_selected_proxies(user_id)
    keyboard = payment_keyboard(proxies, selected_proxies)
    await bot.send_message(chat_id=message.chat.id, text="Select proxies to pay for:", reply_markup=keyboard)
 """
# src/bot/handlers/payment_handlers.py
from aiogram import types
from src.bot.bot_setup import dp, bot
from src.utils.keyboards import payment_keyboard
from src.utils.proxy_utils import toggle_proxy_selection, get_selected_proxies, get_user_proxies
from src.services.payment_service import process_payment, confirm_payment

@dp.callback_query_handler(lambda c: c.data.startswith('toggle_proxy'))
async def handle_toggle_proxy(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    proxy_id = int(callback_query.data.split(':')[1])
    toggle_proxy_selection(user_id, proxy_id)
    proxies = get_user_proxies(user_id)
    selected_proxies = get_selected_proxies(user_id)
    keyboard = payment_keyboard(proxies, selected_proxies)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer()
    
@dp.callback_query_handler(lambda c: c.data == 'confirm_payment')
async def handle_confirm_payment(callback_query: types.CallbackQuery):
    payment_id = int(callback_query.data.split(':')[1])
    await confirm_payment(payment_id)
    await callback_query.message.edit_text("Payment confirmed.")
    await callback_query.answer()

# src/bot/handlers/payment_handlers.py
from aiogram import types
from src.utils.keyboards import payment_keyboard
from src.utils.proxy_utils import toggle_proxy_selection, get_selected_proxies, get_user_proxies
from src.services.payment_service import process_payment

@dp.callback_query_handler(lambda c: c.data.startswith('pay_proxy'))
async def handle_pay_proxy(callback_query: types.CallbackQuery):
    proxy_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id
    # Assume a default payment period or let the user choose
    payment_period = '1 month'  # Example: 1 month
    await process_payment(user_id, [proxy_id], payment_period)
    await callback_query.message.edit_text("Payment initiated. Please wait for confirmation.")
    await callback_query.answer()

