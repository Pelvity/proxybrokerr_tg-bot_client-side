import json
import pytz
from datetime import datetime
import logging
from typing import Optional, Tuple
from typing import List


from src.db.models.db_models import User, UserType, DBProxy, UserHistory
from src.bot.config import USER_TIMEZONE
from sqlalchemy.orm.exc import NoResultFound
    
USER_TIMEZONE = 'Europe/Warsaw'

class UserRepository:
    def __init__(self, session):  # Inject the session
        self.session = session

    def get_or_create_user(self, message, user_type=UserType.TELEGRAM.value):
        try:
            timezone = pytz.timezone(USER_TIMEZONE)

            if user_type == UserType.TELEGRAM.value:
                user_data = {
                    'telegram_user_id': message.from_user.id,
                    'telegram_chat_id': message.chat.id,
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'joined_at': message.date.astimezone(pytz.utc),
                    'last_message_at': message.date.astimezone(pytz.utc),
                    'user_type': user_type
                }
            else:
                user_data = {
                    'user_type': user_type,
                    'joined_at': datetime.now(pytz.utc),
                }

            user = self.session.query(User).filter_by(telegram_user_id=user_data['telegram_user_id']).first()
            
            if not user:
                user = User(**user_data)
                self.session.add(user)
                self.session.flush()  # This will assign an ID if it's a new user
            else:
                self._update_user_and_log_history(user, user_data, timezone)

            # Explicitly load all the attributes we need
            self.session.refresh(user)
            
            # Create a dictionary with all the user data we need
            user_dict = {
                'id': user.id,
                'telegram_user_id': user.telegram_user_id,
                'telegram_chat_id': user.telegram_chat_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'joined_at': user.joined_at,
                'last_message_at': user.last_message_at,
                'user_type': user.user_type
            }

            return user_dict

        except Exception as e:
            logging.exception(f"Error getting or creating user: {e}")
            self.session.rollback()
            return None
    
    
    def get_or_create_user_by_username(self, session, username: str) -> Optional[User]:
        try:
            username = username.lstrip('@')
            user = session.query(User).filter_by(username=username).first()
            if user is None:
                user = User(username=username, user_type=UserType.TELEGRAM.value)
                session.add(user)
                session.commit()
                print(f"Created new User with username: {username}")
            return user
        except Exception as e:
            print(f"Error getting or creating user by username: {e}")
            return None
        
    def _update_user_and_log_history(self, user, user_data, timezone):
        """Updates user attributes and logs changes to UserHistory."""
        for field in ['telegram_chat_id', 'username', 'first_name', 'last_name', 'user_type']:
            old_value = getattr(user, field)
            new_value = user_data.get(field)

            if old_value != new_value:
                history_entry = UserHistory(
                    user_id=user.id,
                    timestamp=datetime.now(pytz.utc),  # Log timestamps in UTC
                    action=f"{field}_changed",
                    details={
                        "old_value": old_value,
                        "new_value": new_value
                    }
                )
                self.session.add(history_entry)

                setattr(user, field, new_value)  # Update the user attribute

        user.last_message_at = user_data.get('last_message_at', datetime.now(pytz.utc))
        self.session.commit()

    def update_user(self, user, message):
        """Updates user attributes based on message data."""
        try:
            timezone = pytz.timezone(USER_TIMEZONE)
            if user['telegram_chat_id'] != message.chat.id:
                user['telegram_chat_id'] = message.chat.id

            user['last_message_at'] = message.date.astimezone(pytz.utc)  # Convert to UTC before saving
            self.session.commit()

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

    def get_all_users(self) -> Tuple[List[User], List[User]]:
        active_users = self.session.query(User).filter_by(is_active=True).all()
        inactive_users = self.session.query(User).filter_by(is_active=False).order_by(User.id.desc()).limit(5).all()
        return active_users, inactive_users
    
    def get_active_users(self) -> List[User]:
        return self.session.query(User).filter_by(is_active=True).all()

    def get_inactive_users(self) -> List[User]:
        return self.session.query(User).filter_by(is_active=False).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Gets a user by ID."""
        return self.session.query(User).get(user_id)
    
    def get_user_by_telegram_user_id(self, telegram_user_id: int) -> Optional[User]:
        """Gets a user by Telegram user ID."""
        try:
            return self.session.query(User).filter_by(telegram_user_id=telegram_user_id).one()
        except NoResultFound:
            return None
        
    def _extract_user_data(self, message, user_type) -> dict:
        """Extracts user data from the message."""
        return {
            'telegram_user_id': message.from_user.id,
            'telegram_chat_id': message.chat.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'joined_at': message.date.astimezone(pytz.utc),
            'last_message_at': message.date.astimezone(pytz.utc),
            'user_type': user_type
        }
        
    def _get_or_create_user_by_telegram_id(self, user_data: dict) -> Tuple[User, bool]:
        """Gets or creates a User by Telegram ID."""
        try:
            user = self.session.query(User).filter_by(telegram_user_id=user_data['telegram_user_id']).one()
            return user, False
        except NoResultFound:
            user = User(**user_data)
            self.session.add(user)
            self.session.commit()
            return user, True
        
    def _update_user_and_log_history(self, user, user_data, timezone):
        """Updates user attributes and logs changes to UserHistory."""
        for field in ['telegram_chat_id', 'username', 'first_name', 'last_name', 'user_type']:
            old_value = getattr(user, field)
            new_value = user_data.get(field)

            if old_value != new_value:
                history_entry = UserHistory(
                    user_id=user.id,
                    timestamp=datetime.now(pytz.utc),  # Log timestamps in UTC
                    action=f"{field}_changed",
                    details=json.dumps({  # Serialize the details dictionary to a JSON string
                        "old_value": old_value,
                        "new_value": new_value
                    })
                )
                self.session.add(history_entry)

                setattr(user, field, new_value)  # Update the user attribute

        user.last_message_at = user_data.get('last_message_at', datetime.now(pytz.utc))
        self.session.commit()