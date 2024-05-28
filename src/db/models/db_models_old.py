from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, DECIMAL, BigInteger, ForeignKeyConstraint
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


class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=False, nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    user_type = Column(String(255), default=UserType.TELEGRAM.value)
    telegram_user_id = Column(BigInteger, unique=False, nullable=True)
    telegram_chat_id = Column(BigInteger, unique=False, nullable=True)
    
    joined_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Identity Confirmation (Phone)
    phone_number_confirmed = Column(Boolean, default=False) 

    # Identity Confirmation (Bank Transfer)
    bank_transfer_confirmed = Column(Boolean, default=False)

    #proxies = relationship("DBProxy", backref="user")
    payments = relationship("Payment", backref="user")
    phone_numbers = relationship("UserPhoneNumber", backref="user")
    bank_transfers = relationship("BankTransferConfirmation", backref="user")


class UserHistory(Base):
    __tablename__ = 'UserHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    user_type = Column(String(255))
    changed_field = Column(String(50))
    old_value = Column(String(255))
    new_value = Column(String(255))

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


class BankTransferConfirmation(Base):
    __tablename__ = 'BankTransferConfirmations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    bank_name = Column(String(255), nullable=False)  
    transaction_id = Column(String(255), nullable=False)
    confirmed = Column(Boolean, default=False) 
    created_at = Column(DateTime, default=datetime.now)


class DBProxy(Base):
    __tablename__ = 'Proxies'
    id = Column(String(255), primary_key=True) 
    phone_id = Column(Integer, ForeignKey('Phones.id'), nullable=True)
    #user_id = Column(Integer, ForeignKey('Users.id'), nullable=True) 
    name = Column(String(255))
    expiration_date = Column(DateTime)
    #hours_left = Column(Integer)
    tariff_plan = Column(String(255))
    tariff_expiration_date = Column(DateTime, default=datetime(2000, 1, 1))
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
    id = Column(String(255), primary_key=True)  # Connection ID (from the proxy service)
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    
    created_timestamp = Column(DateTime, default=datetime.now)
    updated_timestamp = Column(DateTime, default=datetime.now)
    name = Column(String(255))
    description = Column(String(255))
    host = Column(String(255))
    port = Column(Integer)
    login = Column(String(255))
    password = Column(String(255))
    connection_type = Column(String(255))
    active = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    proxy = relationship("DBProxy", back_populates="connections")
    user = relationship("User", backref="connections")  # Add user relationship
    histories = relationship("ConnectionHistory", back_populates="proxy_connection")


class Payment(Base):
    __tablename__ = 'Payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    proxy_id = Column(String(255), ForeignKey('Proxies.id'))
    amount = Column(DECIMAL(10, 2))
    payment_date = Column(DateTime, default=datetime.now)
    status = Column(String(255), default='pending')
    txid = Column(String(255))
    admin_message_id = Column(BigInteger, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


""" class ConnectionHistory(Base):
    __tablename__ = 'ConnectionHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey('ProxyConnections.id'), nullable=False)
    host = Column(String(255))
    port = Column(Integer)
    login = Column(String(255))
    password = Column(String(255))
    start_datetime = Column(DateTime, default=datetime.now(timezone.utc))
    end_datetime = Column(DateTime, nullable=True)

    connection = relationship("DBProxyConnection", back_populates="histories") """
    
    

class ConnectionHistory(Base):
    __tablename__ = 'ConnectionHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)  # Keep user_id 

    # Connection data fields (replace with your actual fields)
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