from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, DECIMAL, BigInteger, ForeignKeyConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.orm.exc import NoResultFound

from src.db.azure_db import Base

current_datetime_utc = datetime.now(timezone.utc)


class UserType(Enum):
    TELEGRAM = 'telegram'
    WEBSITE = 'website'
    BOTH = 'both' 


class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=True)  # Now unique
    email = Column(String(255), unique=True, nullable=True)  # Added email
    password_hash = Column(String(255), nullable=True)  # Added password_hash
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    user_type = Column(String(255), default=UserType.TELEGRAM.value)
    telegram_user_id = Column(BigInteger, unique=True, nullable=True)
    telegram_chat_id = Column(BigInteger, unique=True, nullable=True)
    joined_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    phone_number_confirmed = Column(Boolean, default=False)
    bank_transfer_confirmed = Column(Boolean, default=False)
    #subscription_id = Column(Integer, ForeignKey('Subscriptions.id'), nullable=True)  # Added subscription_id

    # Relationships
    payments = relationship("Payment", backref="user")
    phone_numbers = relationship("UserPhoneNumber", backref="user")
    bank_transfers = relationship("BankTransferConfirmation", backref="user")
    #subscription = relationship("Subscription", backref="users")  # Added relationship for subscription


# class UserHistory(Base):
#     __tablename__ = 'UserHistory'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
#     timestamp = Column(DateTime, default=datetime.now(timezone.utc))
#     event_type = Column(String(255))  # Changed to 'event_type'
#     details = Column(String(255), nullable=True)  # Changed to 'details'

#     user = relationship("User", backref="history_entries") 

class UserHistory(Base):
    __tablename__ = 'UserHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    action = Column(String(50))  # Action or event (e.g., 'username_changed', 'login', 'payment_made')
    details = Column(Text, nullable=True)  # Flexible JSON field for additional details

    user = relationship("User", backref="history_entries")


class Phone(Base):
    __tablename__ = 'Phones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(255), nullable=False)
    imei = Column(String(255), unique=True, nullable=False)
    description = Column(String(255))
    date_of_buying = Column(DateTime)
    active = Column(Boolean, default=True)
    sim_card_id = Column(Integer, ForeignKey('SimCards.id'), nullable=True)

    sim_card = relationship("SimCard", back_populates="phones")
    proxies = relationship("DBProxy", back_populates="phone")


class SimCard(Base):
    __tablename__ = 'SimCards'
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(255), unique=True, nullable=False)
    iccid = Column(String(255), unique=True, nullable=False)

    phones = relationship("Phone", back_populates="sim_card")


class UserPhoneNumber(Base):
    __tablename__ = 'UserPhoneNumbers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    phone_number = Column(String(255))
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship("User", backref="phone_numbers")  


class BankTransferConfirmation(Base):
    __tablename__ = 'BankTransferConfirmations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    bank_name = Column(String(255), nullable=False)
    transaction_id = Column(String(255), nullable=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", backref="bank_transfers")


class DBProxy(Base):
    __tablename__ = 'Proxies'
    id = Column(String(255), primary_key=True)
    phone_id = Column(Integer, ForeignKey('Phones.id'), nullable=True)
    name = Column(String(255))
    expiration_date = Column(DateTime)
    tariff_plan = Column(String(255))
    tariff_expiration_date = Column(DateTime)  
    tariff_days_left = Column(Integer)
    device_model = Column(String(255))
    active = Column(Boolean)
    service_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    service_account_login = Column(String(255), nullable=True)

    phone = relationship("Phone", back_populates="proxies")
    connections = relationship("DBProxyConnection", back_populates="proxy")


class DBProxyConnection(Base):
    __tablename__ = 'ProxyConnections'
    id = Column(String(255), primary_key=True) 
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    created_timestamp = Column(DateTime, default=datetime.now)
    updated_timestamp = Column(DateTime, default=datetime.now)
    name = Column(String(255), nullable=True)  
    description = Column(String(255), nullable=True) 
    host = Column(String(255))
    port = Column(Integer)
    login = Column(String(255), nullable=True) 
    password = Column(String(255), nullable=True)  
    connection_type = Column(String(255))
    active = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    proxy = relationship("DBProxy", back_populates="connections")
    user = relationship("User", backref="connections") 
    histories = relationship("ConnectionHistory", back_populates="proxy_connection")


# class Subscription(Base):
#     __tablename__ = 'Subscriptions'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255))
#     description = Column(String(255), nullable=True)  
#     price = Column(DECIMAL(10, 2))
#     duration_days = Column(Integer)
#     active = Column(Boolean, default=True)

    # Relationships (backref from User model)


class Payment(Base):
    __tablename__ = 'Payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=True)  # Allow null for account top-ups
    amount = Column(DECIMAL(10, 2))
    payment_date = Column(DateTime, default=datetime.now)
    status = Column(String(255), default='pending')
    txid = Column(String(255), nullable=True) 
    admin_message_id = Column(BigInteger, nullable=True)
    start_date = Column(Date, nullable=True) 
    end_date = Column(Date, nullable=True) 

    user = relationship("User", backref="payments")
    proxy = relationship("DBProxy", backref="payments")  

class ConnectionHistory(Base):
    __tablename__ = 'ConnectionHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True) 

    name = Column(String(255))
    description = Column(String(255))
    host = Column(String(255))
    port = Column(Integer)
    login = Column(String(255))
    password = Column(String(255))
    connection_type = Column(String(255))
    active = Column(Boolean, default=True) 

    start_datetime = Column(DateTime, default=datetime.now(timezone.utc))
    end_datetime = Column(DateTime, nullable=True)

    proxy_connection = relationship("DBProxyConnection", back_populates="histories")
    user = relationship("User", backref="connection_histories")