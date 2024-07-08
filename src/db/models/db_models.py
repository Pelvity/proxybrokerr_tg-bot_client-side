from sqlalchemy import CheckConstraint, Column, Integer, String, Boolean, ForeignKey, DECIMAL, BigInteger, ForeignKeyConstraint, Text, Enum as SQLAEnum
from sqlalchemy.dialects.mssql import SMALLDATETIME
from sqlalchemy.dialects.mysql import DATETIME as MYSQLDATETIME
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum

from src.db.azure_db import Base as AzureBase
from src.db.aws_db import Base as AWSBase

def current_datetime_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)

class UserType(Enum):
    TELEGRAM = 'telegram'
    WEBSITE = 'website'

class ChangeType(Enum):
    CONNECTION_DATA_CHANGE = 'connection_data_change'
    USER_CONNECTION_CHANGE = 'user_connection_change'
    DEVICE_CONNECTION_CHANGE = 'device_connection_change'
    NAME = 'name'
    DESCRIPTION = 'description'
    HOST = 'host'
    PORT = 'port'
    LOGIN = 'login'
    PASSWORD = 'password'
    CONNECTION_TYPE = 'connection_type'
    ACTIVE = 'active'
    OTHER = 'other'  # For any other changes not covered by the above types

class UserConnectionChangeType(Enum):
    ASSIGNED = 'assigned'
    UNASSIGNED = 'unassigned'
    REASSIGNED = 'reassigned'

class DeviceProxyChangeType(Enum):
    PHONE_CHANGE = 'phone_change'
    SIM_CARD_CHANGE = 'sim_card_change'

# Choose the appropriate base class based on the database type
from src.bot.config import DATABASE_TYPE

if DATABASE_TYPE == 'azure':
    Base = AzureBase
    DateTimeType = SMALLDATETIME
elif DATABASE_TYPE == 'aws':
    Base = AWSBase
    DateTimeType = MYSQLDATETIME
else:
    raise ValueError("Unsupported DATABASE_TYPE. Please set it to either 'azure' or 'aws'.")

class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=False, nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    user_type = Column(String(255), default=UserType.TELEGRAM.value)
    telegram_user_id = Column(BigInteger, unique=False, nullable=True)
    telegram_chat_id = Column(BigInteger, unique=False, nullable=True)
    joined_at = Column(DateTimeType, nullable=True, default=current_datetime_utc)
    last_message_at = Column(DateTimeType, nullable=True, default=current_datetime_utc)
    is_active = Column(Boolean, default=True)
    phone_number_confirmed = Column(Boolean, default=False) 
    bank_transfer_confirmed = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)  

    payments = relationship("Payment", backref="user_payments")
    phone_numbers = relationship("UserPhoneNumber", backref="user")
    connections = relationship("DBProxyConnection", back_populates="user")
    old_connection_changes = relationship("UserConnectionChange", foreign_keys="[UserConnectionChange.old_user_id]", back_populates="old_user")
    new_connection_changes = relationship("UserConnectionChange", foreign_keys="[UserConnectionChange.new_user_id]", back_populates="new_user")
    connection_changes = relationship("ConnectionDataChange", back_populates="user")
    history_entries = relationship("UserHistory", back_populates="user")

class Phone(Base):
    __tablename__ = 'Phones' 
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(255), nullable=False)
    imei = Column(String(255), unique=True, nullable=False)
    description = Column(String(255))
    date_of_buying = Column(DateTimeType, default=current_datetime_utc)
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
    created_at = Column(DateTimeType, default=current_datetime_utc)
    updated_at = Column(DateTimeType, default=current_datetime_utc)

class DBProxy(Base):
    __tablename__ = 'Proxies'
    id = Column(String(255), primary_key=True) 
    phone_id = Column(Integer, ForeignKey('Phones.id'), nullable=True)
    name = Column(String(255))
    tariff_plan = Column(String(255))
    tariff_expiration_date = Column(DateTimeType, default=datetime(2000, 1, 1))
    device_model = Column(String(255))
    active = Column(Boolean)
    service_name = Column(String(255))
    created_at = Column(DateTimeType, default=current_datetime_utc)
    updated_at = Column(DateTimeType, default=current_datetime_utc)
    service_account_login = Column(String(255), nullable=True)

    phone = relationship("Phone", back_populates="proxies")
    connections = relationship("DBProxyConnection", back_populates="proxy")
    device_proxy_change_histories = relationship("DeviceProxyChangeHistory", back_populates="proxy")
    
class DBHost(Base):
    __tablename__ = 'Hosts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_ip = Column(String(255), nullable=False, unique=True)
    country_code = Column(String(10), nullable=False)
    country_name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)

    connections = relationship('DBProxyConnection', back_populates='host')

class DBProxyConnection(Base):
    __tablename__ = 'ProxyConnections'
    id = Column(String(255), primary_key=True)  # Connection ID (from the proxy service)
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    host_id = Column(Integer, ForeignKey('Hosts.id'), nullable=True)  # Foreign key to Host table
    expiration_date = Column(DateTimeType, default=current_datetime_utc)
    created_datetime = Column(DateTimeType, default=current_datetime_utc)
    updated_datetime = Column(DateTimeType, default=current_datetime_utc)
    name = Column(String(255))
    description = Column(String(255))
    port = Column(Integer)
    login = Column(String(255))
    password = Column(String(255))
    connection_type = Column(String(255))
    active = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)

    proxy = relationship("DBProxy", back_populates="connections")
    user = relationship("User", back_populates="connections")
    user_change_histories = relationship("UserConnectionChange", back_populates="connection")
    payments = relationship("Payment", back_populates="connection")
    changes = relationship("ConnectionDataChange", back_populates="connection")
    device_proxy_change_histories = relationship("DeviceProxyChangeHistory", back_populates="connection")
    host = relationship("Host", back_populates="connections")  # Relationship to Host

class Payment(Base):
    __tablename__ = 'Payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'))
    amount = Column(DECIMAL(10, 2))
    payment_date = Column(DateTimeType, default=current_datetime_utc)
    status = Column(String(255), default='pending')
    payment_method = Column(String(255))  
    start_date = Column(DateTimeType, nullable=True, default=current_datetime_utc)
    end_date = Column(DateTimeType, nullable=True, default=current_datetime_utc)

    connection = relationship("DBProxyConnection", back_populates="payments")

class CryptoPayment(Base):
    __tablename__ = 'CryptoPayments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey('Payments.id'))
    txid = Column(String(255), nullable=False)

    payment = relationship("Payment", backref="crypto_payment")

class BankTransferPayment(Base):
    __tablename__ = 'BankTransferPayments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bank_name = Column(String(255), nullable=False)  
    payment_id = Column(Integer, ForeignKey('Payments.id'))
    transaction_id = Column(String(255), nullable=False)

    payment = relationship("Payment", backref="bank_transfer_payment")

class UserHistory(Base):
    __tablename__ = 'UserHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    timestamp = Column(DateTimeType, default=current_datetime_utc)
    action = Column(String(50))  # Action/Event (e.g., 'username_changed', 'profile_updated')
    details = Column(Text, nullable=True)  # JSON details for more information

    user = relationship("User", back_populates="history_entries")
    
class UserConnectionChange(Base):
    __tablename__ = 'UserConnectionChange'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    old_user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    new_user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    change_type = Column(String(50))  # e.g., 'assigned', 'unassigned'
    change_date = Column(DateTimeType, default=current_datetime_utc)

    connection = relationship("DBProxyConnection", back_populates="user_change_histories")
    old_user = relationship("User", foreign_keys=[old_user_id], back_populates="old_connection_changes")
    new_user = relationship("User", foreign_keys=[new_user_id], back_populates="new_connection_changes")

class ConnectionDataChange(Base):
    __tablename__ = 'ConnectionDataChange'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    change_type = Column(String(255), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    change_date = Column(DateTimeType, default=current_datetime_utc)

    connection = relationship("DBProxyConnection", back_populates="changes")
    user = relationship("User", back_populates="connection_changes")

class DeviceProxyChangeHistory(Base):
    __tablename__ = 'DeviceProxyChangeHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=False)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    change_type = Column(String(255), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    change_date = Column(DateTimeType, default=current_datetime_utc)

    proxy = relationship("DBProxy", back_populates="device_proxy_change_histories")
    connection = relationship("DBProxyConnection", back_populates="device_proxy_change_histories")
