from peewee import *

db = SqliteDatabase('your_database.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = IntegerField(unique=True)
    chat_id = IntegerField()
    username = CharField(null=True)
    first_name = CharField()
    last_name = CharField(null=True)
    joined_at = DateTimeField()

class Purchase(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='purchases')
    proxy_id = CharField()
    purchase_date = DateTimeField()
    expiry_date = DateTimeField()
    price = DecimalField()

class Proxy(BaseModel):
    id = CharField(primary_key=True)
    description = TextField()
    price = DecimalField()
    status = CharField()