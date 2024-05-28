import pytz
from datetime import datetime
import logging
from typing import Optional, Tuple
from typing import List

from src.db.models.db_models import User, UserType, UserHistory, DBProxy
from src.bot.config import USER_TIMEZONE
    
USER_TIMEZONE = 'Europe/Warsaw'

class UserRepository:
    def __init__(self, session):  # Inject the session
        self.session = session

    def get_or_create_user(self, message, user_type=UserType.TELEGRAM.value):
        """Gets or creates a User, tracking changes in UserHistory."""
        try:
            timezone = pytz.timezone(USER_TIMEZONE)

            if user_type == UserType.TELEGRAM.value:
                user_data = {
                    'telegram_user_id': message.from_user.id,
                    'telegram_chat_id': message.chat.id,
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'joined_at': message.date.astimezone(timezone),
                    'last_message_at': message.date.astimezone(timezone),
                    'user_type': user_type
                }
            else:
                user_data = {
                    'user_type': user_type,
                    'joined_at': datetime.now(timezone),
                }

            user, created = User.get_or_create(self.session, **user_data)

            if not created:
                # Check for changes and log to UserHistory (including user_type)
                for field in ['telegram_chat_id', 'username', 'first_name', 'last_name']:
                    old_value = getattr(user, field)
                    new_value = user_data.get(field)

                    if old_value != new_value:
                        history_entry = UserHistory(
                            user_id=user.id,
                            timestamp=datetime.now(timezone.utc),
                            user_type=user_type,
                            changed_field=field,
                            old_value=old_value,
                            new_value=new_value
                        )
                        self.session.add(history_entry)

                # Update user attributes 
                user.telegram_chat_id = user_data.get('telegram_chat_id')
                user.username = user_data.get('username')
                user.first_name = user_data.get('first_name')
                user.last_name = user_data.get('last_name')
                user.last_message_at = user_data['last_message_at']
                self.session.commit()

            return user

        except Exception as e:
            logging.exception(f"Error getting or creating user: {e}")
            return None

    def get_or_create_user_by_username(self, session, username: str) -> Optional[User]:
        """Gets or creates a User based on username, handling potential "@" prefix."""
        try:
            username = username.lstrip('@')  # Remove leading "@" if present

            user = session.query(User).filter_by(username=username).first()
            if user is None:
                user = User(username=username)  # Basic User creation
                session.add(user)
                session.commit()
                print(f"Created new User with username: {username}")
            return user

        except Exception as e:
            print(f"Error getting or creating user by username: {e}")
            return None 
        
    def update_user(self, user, message):
        """Updates user attributes based on message data."""
        try:
            timezone = pytz.timezone(USER_TIMEZONE)

            if user.telegram_chat_id != message.chat.id:
                user.telegram_chat_id = message.chat.id
            if user.last_message_at != message.date.astimezone(timezone):
                user.last_message_at = message.date.astimezone(timezone)

            self.session.commit()  # Commit the changes

        except Exception as e:
            logging.exception(f"Error updating user in database: {e}")
            

    def get_or_create_user_by_telegram_data(
        self, 
        session, 
        telegram_user_id: int, 
        username: str, 
        chat_id: int, 
        joined_at: datetime
    ) -> Tuple[User, bool]:
        """Gets or creates a User based on Telegram data, handling "@" in usernames."""

        username = username.lstrip('@')  # Normalize username 

        try:
            user = session.query(User).filter_by(telegram_user_id=telegram_user_id).first()
            if user is None:
                user = User(
                    telegram_user_id=telegram_user_id, 
                    username=username, 
                    telegram_chat_id=chat_id, 
                    joined_at=joined_at
                )
                session.add(user)
                session.commit()
                print(f"Created new user with Telegram ID: {telegram_user_id}")
                return user, True
            return user, False
        except Exception as e:
            print(f"Error getting or creating user: {e}")
            return None, False

    # def get_user_proxies(self, user_id: int) -> List[DBProxy]:
    #     return (
    #         self.session.query(DBProxy)
    #         .filter_by(user_id=user_id)
    #         .all()
    #     )