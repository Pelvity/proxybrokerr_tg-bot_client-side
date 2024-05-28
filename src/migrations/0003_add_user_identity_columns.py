# migrations/0003_add_user_identity_columns.py

from peewee import *
from playhouse.migrate import *

def migrate(migrator, database, fake=False, **kwargs):
    migrator.add_column('user', 'user_id', IntegerField(unique=True, null=True))
    migrator.add_column('user', 'phone_number', CharField(null=True))
    migrator.add_column('user', 'bank_name', CharField(null=True))
    migrator.add_column('user', 'transaction_id', CharField(null=True))
    migrator.add_column('user', 'identity_confirmed', BooleanField(default=False))

def rollback(migrator, database, fake=False, **kwargs):
    migrator.drop_column('user', 'user_id')
    migrator.drop_column('user', 'phone_number')
    migrator.drop_column('user', 'bank_name')
    migrator.drop_column('user', 'transaction_id')
    migrator.drop_column('user', 'identity_confirmed')
