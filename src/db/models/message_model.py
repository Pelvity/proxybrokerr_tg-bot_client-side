# In src/db/models/message_model.py
from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AdminMessage(Base):
    __tablename__ = 'admin_messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    admin_message_id = Column(BigInteger)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime)
