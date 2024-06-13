import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentTypes
from src.bot.bot_setup import bot, dp, database
from src.db.models.db_models import User
from src.bot.config import ADMIN_CHAT_ID
from src.utils.keyboards import admin_main_menu
from aiogram.dispatcher.filters.state import State, StatesGroup
from src.db.repositories.user_repositories import UserRepository
from src.middlewares.forward_to_admin_middleware import forwarded_message_mapping

class AdminStates(StatesGroup):
    waiting_for_message = State()

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID, commands=['start'])
async def admin_start_command(message: types.Message):
    await message.reply("Welcome, admin!", reply_markup=admin_main_menu())

# @dp.message_handler(commands=['start'])
# async def admin_start_command(message: types.Message):
#     if message.from_user.id == ADMIN_CHAT_ID:
#         await message.reply("Welcome to ADMIN!", reply_markup=admin_main_menu())

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "👥 My Clients")
async def admin_my_clients_command(message: types.Message):
    with database.get_session() as session:
        user_repository = UserRepository(session) 
        clients = user_repository.get_all_users()  # Use the repository method

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

    with database.get_session() as session:
        user_repository = UserRepository(session)
        client = user_repository.get_user_by_id(client_id)  # Use repository method

    if client:
        await state.update_data(selected_client=client)
        await AdminStates.waiting_for_message.set()

        # Create a keyboard with a cancel button
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))

        await query.message.reply("Please enter the message you want to send to the client:", reply_markup=keyboard)
    else:
        await query.message.reply("Client not found.")
        
@dp.callback_query_handler(lambda query: query.data == "cancel")
async def handle_cancel(query: types.CallbackQuery, state: FSMContext):
    if query.from_user.id == ADMIN_CHAT_ID:
        await state.finish()
        await query.message.reply("Action canceled.", reply_markup=admin_main_menu())
    await bot.answer_callback_query(query.id)  # Acknowledge the callback query

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID, state=AdminStates.waiting_for_message)
async def admin_send_message_to_client(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client = data.get('selected_client')

    if client:
        await bot.send_message(chat_id=client.telegram_chat_id, text=message.text)
        await message.reply(
            f"Message sent to {client.first_name} {client.last_name} "
            f"(@{client.username}, Telegram ID: {client.telegram_user_id})."
        )
        await state.finish()
    else:
        await message.reply("Client not found or not selected.")
        await state.finish()


# @dp.message_handler(lambda message: message.reply_to_message and message.from_user.id == ADMIN_CHAT_ID)
@dp.message_handler(content_types=ContentTypes.ANY)
async def handle_admin_reply(message: types.Message):
    if message.reply_to_message and message.from_user.id == ADMIN_CHAT_ID:
        original_message = forwarded_message_mapping.get(message.reply_to_message.message_id)
        if original_message:
            original_user_chat_id = original_message.chat.id
            try:
                if message.content_type == 'text':
                    await bot.send_message(chat_id=original_user_chat_id, text=message.text)
                elif message.content_type == 'photo':
                    photo = message.photo[-1]
                    await bot.send_photo(chat_id=original_user_chat_id, photo=photo.file_id, caption=message.caption)
                elif message.content_type == 'document':
                    await bot.send_document(chat_id=original_user_chat_id, document=message.document.file_id, caption=message.caption)
                elif message.content_type == 'sticker':
                    await bot.send_sticker(chat_id=original_user_chat_id, sticker=message.sticker.file_id)
                elif message.content_type == 'audio':
                    await bot.send_audio(chat_id=original_user_chat_id, audio=message.audio.file_id, caption=message.caption)
                elif message.content_type == 'video':
                    await bot.send_video(chat_id=original_user_chat_id, video=message.video.file_id, caption=message.caption)
                elif message.content_type == 'voice':
                    await bot.send_voice(chat_id=original_user_chat_id, voice=message.voice.file_id, caption=message.caption)
                elif message.content_type == 'contact':
                    await bot.send_contact(chat_id=original_user_chat_id, phone_number=message.contact.phone_number, first_name=message.contact.first_name, last_name=message.contact.last_name)
                elif message.content_type == 'location':
                    await bot.send_location(chat_id=original_user_chat_id, latitude=message.location.latitude, longitude=message.location.longitude)
                elif message.content_type == 'venue':
                    await bot.send_venue(chat_id=original_user_chat_id, latitude=message.venue.location.latitude, longitude=message.venue.location.longitude, title=message.venue.title, address=message.venue.address)
                else:
                    await bot.send_message(chat_id=original_user_chat_id, text="Unsupported content type.")
                
                await message.reply("Your reply has been sent to the user.")
            except Exception as e:
                logging.exception(f"Error sending reply to user: {e}")
                await message.reply("Failed to send the reply to the user.")
        else:
            await message.reply("The original user message could not be found.")
