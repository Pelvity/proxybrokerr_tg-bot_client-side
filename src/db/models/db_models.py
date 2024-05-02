from peewee import *
from datetime import datetime

class User(Model):
    id = AutoField(unique=True)
    chat_id = IntegerField(null=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    joined_at = DateTimeField(null=True)
    last_message_at = DateTimeField(null=True)
    is_active = BooleanField(default=True)

    class Meta:
        database = None  # Set the database attribute to None initially

class DBProxy(Model):
    id = AutoField()
    name = CharField()
    auth_token = CharField(unique=True)
    user = ForeignKeyField(User, backref='proxies', null=True)  # One-to-many relationship with User
    expiration_date = DateTimeField()
    hours_left = IntegerField()
    tariff_plan = CharField()
    tariff_expiration_date = DateTimeField(default=datetime(2000, 1, 1))
    tariff_days_left = IntegerField()
    device_model = CharField()
    active = BooleanField()
    service_name = CharField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def days_left(self):
        return (self.expiration_date - datetime.now().date()).days
    class Meta:
        database = None  # Set the database attribute to None initially

class DBProxyConnection(Model):
    id = CharField(primary_key=True)
    user = ForeignKeyField(User, backref='proxy_connections', null=True)  # One-to-many relationship with User
    proxy = ForeignKeyField(DBProxy, backref='connections')  # One-to-many relationship with DBProxy
    created_timestamp = IntegerField()
    updated_timestamp = IntegerField()
    name = CharField()
    description = CharField()
    ip = CharField()
    port = IntegerField()
    login = CharField()
    password = CharField()
    type = CharField()
    active = BooleanField()

    class Meta:
        database = None  # Set the database attribute to None initially

""" class Purchase(Model):
    id = AutoField()
    user = ForeignKeyField(User, backref='purchases')  # One-to-many relationship with User
    proxy = ForeignKeyField(DBProxy, backref='purchases')  # One-to-many relationship with DBProxy
    purchase_date = DateTimeField()
    expiry_date = DateTimeField()
    price = DecimalField()

    class Meta:
        database = None  # Set the database attribute to None initially
 """

class Payment(Model):
    id = AutoField()
    user = ForeignKeyField(User, backref='payments')
    proxy = ForeignKeyField(DBProxy, backref='payments')
    amount = DecimalField()
    payment_date = DateTimeField(default=datetime.now)
    status = CharField(default='pending')  # pending, confirmed

    class Meta:
        database = None  # Set the database attribute to None initially
        
class DBProxyHistory(Model):
    id = AutoField()
    proxy = ForeignKeyField(DBProxy, backref='history')  # One-to-many relationship with DBProxy
    user = ForeignKeyField(User, backref='proxy_history')  # One-to-many relationship with User
    service_name = CharField()
    name = CharField()
    expiration_date = DateTimeField()
    tariff_plan = CharField()
    tariff_expiration_date = DateTimeField(default=datetime(2000, 1, 1))
    days_left = IntegerField()
    hours_left = IntegerField()
    device_model = CharField()
    active = BooleanField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = None  # Set the database attribute to None initially
