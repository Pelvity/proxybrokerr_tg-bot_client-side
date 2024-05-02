# migrations/0001_initial.py

from peewee import *
from playhouse.migrate import *
from src.db.database import db

def migrate(migrator, database, fake=False, **kwargs):
    last_message_at_field = DateTimeField(null=True)
    is_active_field = BooleanField(default=True)

    migrator.add_column('user', 'last_message_at', last_message_at_field)
    migrator.add_column('user', 'is_active', is_active_field)

def rollback(migrator, database, fake=False, **kwargs):
    migrator.drop_column('user', 'last_message_at')
    migrator.drop_column('user', 'is_active')
