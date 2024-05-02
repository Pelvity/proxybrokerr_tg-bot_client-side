from aiogram import types
from aiogram.dispatcher import FSMContext
from src.bot.bot_setup import bot, dp
from src.db.models.db_models import User
from src.bot.config import ADMIN_CHAT_ID
from src.utils.keyboards import admin_main_menu
from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_message = State()

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID, commands=['start'])
async def admin_start_command(message: types.Message):
    await message.reply("Welcome, admin!", reply_markup=admin_main_menu())

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "👥 My Clients")
async def admin_my_clients_command(message: types.Message):
    clients = User.select()
    if not clients:
        await message.reply("No clients found.")
    else:
        keyboard = types.InlineKeyboardMarkup()
        for client in clients:
            keyboard.add(types.InlineKeyboardButton(
                text=f"{client.first_name} {client.last_name} (@{client.username})",
                callback_data=f"client_{client.id}"
            ))
        await message.reply("Select a client:", reply_markup=keyboard)

@dp.callback_query_handler(lambda query: query.from_user.id == ADMIN_CHAT_ID and query.data.startswith("client_"))
async def admin_client_selected(query: types.CallbackQuery, state: FSMContext):
    client_id = int(query.data.split("_")[1])
    client = User.get_by_id(client_id)
    await state.update_data(selected_client=client)
    await AdminStates.waiting_for_message.set()
    await query.message.reply("Please enter the message you want to send to the client:")

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID, state=AdminStates.waiting_for_message)
async def admin_send_message_to_client(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client = data.get('selected_client')
    await bot.send_message(chat_id=client.chat_id, text=message.text)
    await message.reply(f"Message sent to {client.first_name} {client.last_name} (@{client.username}).")
    await state.finish()


""" PAYMENT """

from src.services.payment_service import confirm_payment

@dp.callback_query_handler(lambda c: c.data.startswith('confirm_payment'))
async def process_confirm_payment_callback(callback_query: types.CallbackQuery):
    payment_id = get_payment_id_from_callback(callback_query)
    
    await confirm_payment(payment_id)
    await bot.answer_callback_query(callback_query.id)
