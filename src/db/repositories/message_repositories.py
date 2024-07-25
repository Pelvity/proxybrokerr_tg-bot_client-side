
from sqlalchemy.orm import Session
from src.db.models.message_model import AdminMessage
from datetime import datetime

class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_admin_message(self, user_id: int, admin_message_id: int):
        admin_message = AdminMessage(
            user_id=user_id,
            admin_message_id=admin_message_id,
            sent_at=datetime.utcnow()
        )
        self.session.add(admin_message)
        self.session.commit()

    def get_unread_admin_messages(self, user_id: int):
        return self.session.query(AdminMessage).filter(
            AdminMessage.user_id == user_id,
            AdminMessage.is_read == False
        ).all()

    def mark_message_as_read(self, message_id: int):
        message = self.session.query(AdminMessage).get(message_id)
        if message:
            message.is_read = True
            self.session.commit()