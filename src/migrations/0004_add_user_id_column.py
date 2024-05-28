# migrations/0004_add_user_id_column.py

from peewee import *
from playhouse.migrate import *

def migrate(migrator, database, fake=False, **kwargs):
    migrator.add_column('user', 'user_id', IntegerField(unique=True, null=True))

def rollback(migrator, database, fake=False, **kwargs):
    migrator.drop_column('user', 'user_id')
