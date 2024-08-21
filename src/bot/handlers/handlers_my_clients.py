import logging
from math import ceil
from aiogram import types
from aiogram.dispatcher import FSMContext
from sqlalchemy.exc import SQLAlchemyError
from aiogram.types import ContentTypes

from src.bot.bot_setup import bot, dp
from src.bot.config import ADMIN_CHAT_ID
from src.utils.keyboards import admin_main_menu
from src.db.aws_db import aws_rds_service
from src.bot.handlers.admin_handlers import AdminStates
from src.middlewares.forward_to_admin_middleware import forwarded_message_mapping

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "My Clients")
async def admin_my_clients_command(message: types.Message, state: FSMContext):
    logging.info(f"My Clients command received from user {message.from_user.id}")
    await show_clients(message, state, is_active=True, page=0)

async def show_clients(message: types.Message, state: FSMContext, is_active: bool, page: int):
    try:
        with aws_rds_service.get_user_repository() as user_repo:
            if is_active:
                clients = user_repo.get_active_users()
            else:
                clients = user_repo.get_inactive_users()
        
        if not clients:
            await message.reply("No clients found.")
            return

        total_pages = ceil(len(clients) / 5)
        start = page * 5
        end = start + 5
        current_page_clients = clients[start:end]

        keyboard = types.InlineKeyboardMarkup()
        for client in current_page_clients:
            status_emoji = "🟢" if is_active else "🔴"
            keyboard.add(types.InlineKeyboardButton(
                text=f"{status_emoji} (@{client.username}) {client.first_name} {client.last_name}",
                callback_data=f"client_{client.id}"
            ))
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("◀️ Previous", callback_data=f"change_page-{is_active}-{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"change_page-{is_active}-{page+1}"))
        if nav_buttons:
            keyboard.row(*nav_buttons)
        
        switch_text = "Show Inactive Clients" if is_active else "Show Active Clients"
        keyboard.add(types.InlineKeyboardButton(switch_text, callback_data=f"switch_clients-{not is_active}-0"))

        client_type = "Active" if is_active else "Inactive"
        text = f"{client_type} clients (Page {page + 1}/{total_pages}):"
        
        data = await state.get_data()
        client_list_message_id = data.get('client_list_message_id')

        if client_list_message_id:
            # Update existing message
            await bot.edit_message_text(
                text=text,
                chat_id=message.chat.id,
                message_id=client_list_message_id,
                reply_markup=keyboard
            )
        else:
            # Send new message and store its ID
            client_list_message = await message.reply(text, reply_markup=keyboard)
            await state.update_data(client_list_message_id=client_list_message.message_id)

    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        await message.reply("An error occurred while fetching clients.")


@dp.callback_query_handler(lambda c: c.data.startswith('change_page'))
async def change_page(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info(f"callback_query.data: {callback_query.data}")
    _, is_active, page = callback_query.data.split('-')
    is_active = is_active.lower() == 'true'
    page = int(page)
    await show_clients(callback_query.message, state, is_active, page)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data.startswith('switch_clients'))
async def switch_clients(callback_query: types.CallbackQuery, state: FSMContext):
    _, is_active, page = callback_query.data.split('-')
    is_active = is_active.lower() == 'true'
    page = int(page)
    await show_clients(callback_query.message, state, is_active, page)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data.startswith('show_inactive_clients_'))
async def show_inactive_clients(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[-1])
    await show_clients(callback_query.message, state, is_active=False, page=page)

@dp.callback_query_handler(lambda c: c.data == 'show_active_clients')
async def show_active_clients(callback_query: types.CallbackQuery, state: FSMContext):
    await show_clients(callback_query.message, state, is_active=True, page=0)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda query: query.from_user.id == ADMIN_CHAT_ID and query.data.startswith("client_"))
async def admin_client_selected(query: types.CallbackQuery, state: FSMContext):
    client_id = int(query.data.split("_")[1])

    with aws_rds_service.get_user_repository() as user_repo:
        client = user_repo.get_user_by_id(client_id)

    if client:
        await state.update_data(selected_client_id=client.id)
        await AdminStates.waiting_for_message.set()

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))

        await query.message.edit_text("Please enter the message you want to send to the client:", reply_markup=keyboard)
    else:
        await query.message.edit_text("Client not found.")

@dp.callback_query_handler(lambda query: query.data == "cancel", state="*")
async def handle_cancel(query: types.CallbackQuery, state: FSMContext):
    if query.from_user.id == ADMIN_CHAT_ID:
        data = await state.get_data()
        client_list_message_id = data.get('client_list_message_id')
        
        if client_list_message_id:
            try:
                await bot.delete_message(chat_id=query.message.chat.id, message_id=client_list_message_id)
            except Exception as e:
                logging.error(f"Failed to delete client list message: {e}")
        
        await state.finish()
    await bot.answer_callback_query(query.id)
    
@dp.message_handler(state=AdminStates.waiting_for_message, content_types=ContentTypes.ANY)
async def admin_send_message_to_client(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client_id = data.get('selected_client_id')
    client_list_message_id = data.get('client_list_message_id')

    if not client_id:
        await message.reply("No client was selected.")
        await state.finish()
        return

    with aws_rds_service.get_user_repository() as user_repo:
        client = user_repo.get_user_by_id(client_id)

    if not client:
        await message.reply("Client not found in the database.")
        await state.finish()
        return

    try:
        if message.content_type == 'text':
            await bot.send_message(chat_id=client.telegram_chat_id, text=message.text)
        elif message.content_type == 'photo':
            photo = message.photo[-1]
            await bot.send_photo(chat_id=client.telegram_chat_id, photo=photo.file_id, caption=message.caption)
        elif message.content_type == 'document':
            await bot.send_document(chat_id=client.telegram_chat_id, document=message.document.file_id, caption=message.caption)
        elif message.content_type == 'sticker':
            await bot.send_sticker(chat_id=client.telegram_chat_id, sticker=message.sticker.file_id)
        elif message.content_type == 'audio':
            await bot.send_audio(chat_id=client.telegram_chat_id, audio=message.audio.file_id, caption=message.caption)
        elif message.content_type == 'video':
            await bot.send_video(chat_id=client.telegram_chat_id, video=message.video.file_id, caption=message.caption)
        elif message.content_type == 'voice':
            await bot.send_voice(chat_id=client.telegram_chat_id, voice=message.voice.file_id, caption=message.caption)
        elif message.content_type == 'contact':
            await bot.send_contact(chat_id=client.telegram_chat_id, phone_number=message.contact.phone_number, first_name=message.contact.first_name, last_name=message.contact.last_name)
        elif message.content_type == 'location':
            await bot.send_location(chat_id=client.telegram_chat_id, latitude=message.location.latitude, longitude=message.location.longitude)
        elif message.content_type == 'venue':
            await bot.send_venue(chat_id=client.telegram_chat_id, latitude=message.venue.location.latitude, longitude=message.venue.location.longitude, title=message.venue.title, address=message.venue.address)
        else:
            await bot.send_message(chat_id=client.telegram_chat_id, text="Unsupported content type.")
        
        await message.reply(
            f"Message sent to {client.first_name} {client.last_name} "
            f"(@{client.username}, Telegram ID: {client.telegram_user_id})."
        )
        
        # Delete the "Select a client:" message if exists
        if client_list_message_id:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=client_list_message_id)
            except Exception as e:
                logging.error(f"Failed to delete client list message: {e}")
                
    except Exception as e:
        logging.error(f"Failed to send message to the client: {e}")
        await message.reply("Failed to send the message to the client.")
    
    await state.finish()


#@dp.message_handler(lambda message: message.reply_to_message and message.from_user.id == ADMIN_CHAT_ID)
@dp.message_handler(content_types=ContentTypes.ANY)
async def handle_admin_reply(message: types.Message):
    logging.info("!! handle_admin_reply")
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