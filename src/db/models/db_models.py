from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DECIMAL, BigInteger, Text, Enum as SQLAEnum
from sqlalchemy.dialects.mssql import SMALLDATETIME
from sqlalchemy.dialects.mysql import DATETIME as MYSQLDATETIME
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash

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
    EXPIRATION_DATE = 'expiration_date'
    CONNECTION_TYPE = 'connection_type'
    ACTIVE = 'active'
    OTHER = 'other'

class UserConnectionChangeType(Enum):
    ASSIGNED = 'assigned'
    UNASSIGNED = 'unassigned'
    REASSIGNED = 'reassigned'

class DeviceProxyChangeType(Enum):
    PHONE_CHANGE = 'phone_change'
    SIM_CARD_CHANGE = 'sim_card_change'

class RentChangeReason(Enum):
    COMPENSATION = 'compensation'
    ADMIN_CORRECTION = 'admin_correction'
    PROMOTIONAL = 'promotional'
    TECHNICAL_ISSUE = 'technical_issue'
    OTHER = 'other'

from src.bot.config import DATABASE_TYPE

if DATABASE_TYPE == 'azure':
    Base = AzureBase
    DateTimeType = SMALLDATETIME
elif DATABASE_TYPE == 'aws':
    Base = AWSBase
    DateTimeType = MYSQLDATETIME
else:
    raise ValueError("Unsupported DATABASE_TYPE. Please set it to either 'azure' or 'aws'.")

class Admin(Base):
    __tablename__ = 'Admins'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    connection_changes = relationship("ConnectionDataChange", back_populates="admin")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

    payments = relationship("Payment", backref="user")
    phone_numbers = relationship("UserPhoneNumber", backref="user")
    connections = relationship("DBProxyConnection", back_populates="user")
    old_connection_changes = relationship("UserConnectionChange", foreign_keys="[UserConnectionChange.old_user_id]", back_populates="old_user")
    new_connection_changes = relationship("UserConnectionChange", foreign_keys="[UserConnectionChange.new_user_id]", back_populates="new_user")
    connection_changes = relationship("ConnectionDataChange", back_populates="user")
    history_entries = relationship("UserHistory", back_populates="user")
    
    def to_dict(self):
        return{
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

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
    description = Column(String(255), nullable=True)

    connections = relationship('DBProxyConnection', back_populates='host')
    
    def to_dict(self):
        return{
            'id': self.id,
            'host_ip': self.host_ip,
            'country_code': self.country_code,
        }

class DBProxyConnection(Base):
    __tablename__ = 'ProxyConnections'
    id = Column(String(255), primary_key=True)
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    host_id = Column(Integer, ForeignKey('Hosts.id'), nullable=True)
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
    host = relationship("DBHost", back_populates="connections")
    
    def to_dict(self):
        return {
            'id': str(self.id) if self.id is not None else None,
            'user': self.user.to_dict() if self.user else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'login': self.login,
            'port': self.port,
            'host': self.host.to_dict() if self.host else None,
            'active': self.active,
            'created_datetime': self.created_datetime.isoformat() if self.created_datetime else None,
        }
        
    def to_simple_dict(self):
        return {
            'id': str(self.id) if self.id is not None else None,
            'login': self.login,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'user': self.user.to_dict() if self.user else None,
            'connection': self.connection.to_simple_dict() if self.connection else None
        }

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
    action = Column(String(50))
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="history_entries")

class UserConnectionChange(Base):
    __tablename__ = 'UserConnectionChange'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    old_user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    new_user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    change_type = Column(SQLAEnum(UserConnectionChangeType))
    change_date = Column(DateTimeType, default=current_datetime_utc)

    connection = relationship("DBProxyConnection", back_populates="user_change_histories")
    old_user = relationship("User", foreign_keys=[old_user_id], back_populates="old_connection_changes")
    new_user = relationship("User", foreign_keys=[new_user_id], back_populates="new_connection_changes")
    
    def get_action_type(self):
        return f"User Connection {self.change_type}"

    def get_description(self):
        old_username = self.old_user.username if self.old_user else 'None'
        new_username = self.new_user.username if self.new_user else 'None'
        return f"{self.change_type.value} - Old User: {old_username}, New User: {new_username}"

    def get_timestamp(self):
        return self.change_date

    def get_user_info(self):
        return self.old_user.username

class DeviceProxyChangeHistory(Base):
    __tablename__ = 'DeviceProxyChangeHistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy_id = Column(String(255), ForeignKey('Proxies.id'), nullable=False)
    change_type = Column(SQLAEnum(DeviceProxyChangeType))
    change_date = Column(DateTimeType, default=current_datetime_utc)

    proxy = relationship("DBProxy", back_populates="device_proxy_change_histories")
    
    def get_action_type(self):
        return "Device Proxy Change"

    def get_description(self):
        return f"{self.change_type.value} - Proxy: {self.proxy.name}"

    def get_timestamp(self):
        return self.change_date

    def get_user_info(self):
        return "N/A"

class ConnectionDataChange(Base):
    __tablename__ = 'ConnectionDataChange'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), ForeignKey('ProxyConnections.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=True)
    admin_id = Column(Integer, ForeignKey('Admins.id'), nullable=True)
    change_type = Column(SQLAEnum(ChangeType))
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_date = Column(DateTimeType, default=current_datetime_utc)
    reason = Column(SQLAEnum(RentChangeReason), nullable=True)

    connection = relationship("DBProxyConnection", back_populates="changes")
    user = relationship("User", back_populates="connection_changes")
    admin = relationship("Admin", back_populates="connection_changes")
    
    def get_action_type(self):
        return "Connection Data Change"

    def get_description(self):
        return f"{self.change_type.value} - Old: {self.old_value}, New: {self.new_value}"

    def get_timestamp(self):
        return self.change_date

    def get_user_info(self):
        if self.admin:
            return f"Admin: {self.admin.username}"
        elif self.user:
            return f"User: {self.user.username}"
        else:
            return "N/A"