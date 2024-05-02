# migrations/0002_add_user_columns.py

from peewee import *
from playhouse.migrate import *
from src.db.database import db

def migrate(migrator, database, fake=False, **kwargs):
    migrate(
        migrator.add_column('user', 'last_message_at', DateTimeField(null=True)),
        migrator.add_column('user', 'is_active', BooleanField(default=True))
    )

def rollback(migrator, database, fake=False, **kwargs):
    migrate(
        migrator.drop_column('user', 'last_message_at'),
        migrator.drop_column('user', 'is_active')
    )
