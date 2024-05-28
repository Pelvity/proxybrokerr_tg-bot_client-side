# src/utils/helpers.py

from src.db.models.db_models import User
from src.bot.bot_setup import bot, client_message_mapping
from ..bot.config import ADMIN_CHAT_ID
import logging
import pytz

async def forward_message_to_admin(message):
    try:
        client_username = message.from_user.username
        client_chat_id = message.chat.id
        client_name = message.from_user.full_name

        if client_username:
            forwarded_message_text = f"@{client_username} (Chat ID: {client_chat_id})\n{message.text}"
        else:
            forwarded_message_text = f"{client_name} (Chat ID: {client_chat_id})\n{message.text}"

        forwarded_message = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=forwarded_message_text)
        client_message_mapping[forwarded_message.message_id] = message
    except Exception as e:
        logging.exception(f"Error forwarding message to admin: {e}")

async def send_reply_to_client(message):
    try:
        if message.reply_to_message and message.reply_to_message.message_id in client_message_mapping:
            client_message = client_message_mapping[message.reply_to_message.message_id]
            reply_text = f"Admin: {message.text}"
            await bot.send_message(chat_id=client_message.chat.id, text=reply_text)
        else:
            logging.warning("Received admin message without a valid reply_to_message")
    except Exception as e:
        logging.exception(f"Error sending reply to client: {e}")


async def save_user_to_database(message, database):
    try:
        # Set the desired timezone (e.g., 'Europe/Warsaw')
        timezone = pytz.timezone('Europe/Warsaw')
        
        # Convert the message date to the desired timezone
        joined_at = message.date.astimezone(timezone)
        last_message_at = message.date.astimezone(timezone)
        
        with database.db.atomic():
            user, created = User.get_or_create(
                id=message.from_user.id,
                defaults={
                    'chat_id': message.chat.id,
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'joined_at': joined_at,
                    'last_message_at': last_message_at,
                    'is_active': True
                }
            )
            if not created:
                user.chat_id = message.chat.id
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                user.last_message_at = last_message_at
                user.save()
    except Exception as e:
        logging.exception(f"Error saving user to database: {e}")

# utils/utils.py

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


""" PAYMENT """


# src/utils/helpers.py
# src/utils/helpers.py
from aiogram.types import CallbackQuery
from src.db.models.db_models import User, DBProxy
from peewee import DoesNotExist

async def get_user_from_callback(callback_query: CallbackQuery) -> User:
    user_id = callback_query.from_user.id
    try:
        user = User.get(User.telegram_user_id == user_id)
        return user
    except DoesNotExist:
        # Handle the case where the user is not found in the database
        return None

async def get_proxy_from_callback(callback_query: CallbackQuery) -> DBProxy:
    # Assuming the callback data for proxy is structured as "action:proxy_id"
    _, proxy_id_str = callback_query.data.split(':')
    proxy_id = int(proxy_id_str)
    try:
        proxy = DBProxy.get(DBProxy.id == proxy_id)
        return proxy
    except DoesNotExist:
        # Handle the case where the proxy is not found in the database
        return None

async def get_payment_period_from_callback(callback_query: CallbackQuery) -> int:
    # Assuming the callback data for payment period is structured as "action:proxy_id:payment_period"
    _, _, payment_period_str = callback_query.data.split(':')
    payment_period = int(payment_period_str)
    return payment_period

async def get_payment_id_from_callback(callback_query: CallbackQuery) -> int:
    # Assuming the callback data for payment ID is structured as "confirm_payment:payment_id"
    _, payment_id_str = callback_query.data.split(':')
    payment_id = int(payment_id_str)
    return payment_id

