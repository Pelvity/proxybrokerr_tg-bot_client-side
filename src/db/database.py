import pymysql
from peewee import *
import boto3
from botocore.exceptions import ClientError
import json
import sys
import os
import base64
from playhouse.migrate import *
import importlib

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

class Database:
    def __init__(self, secret_name, region_name, database_name, database_host):
        self.secret_name = secret_name
        self.region_name = region_name
        self.database_name = database_name
        self.database_host = database_host
        self.secrets = self.get_secret()
        self.db = self.configure_database()

    def get_secret(self):
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=self.region_name)
        try:
            get_secret_value_response = client.get_secret_value(SecretId=self.secret_name)
            print("Successfully retrieved secret from AWS Secrets Manager.")
        except ClientError as e:
            print(f"Failed to retrieve secret: {e}")
            raise e
        else:
            if 'SecretString' in get_secret_value_response:
                return json.loads(get_secret_value_response['SecretString'])
            else:
                decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
                return json.loads(decoded_binary_secret)

    def configure_database(self):
        return MySQLDatabase(
            self.database_name,
            user=self.secrets['username'],
            password=self.secrets['password'],
            host=self.database_host,
            port=3306
        )

    def create_database_if_not_exists(self):
        connection = pymysql.connect(
            host=self.database_host,
            user=self.secrets['username'],
            password=self.secrets['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW DATABASES LIKE '{self.database_name}';")
                result = cursor.fetchone()
                if not result:
                    cursor.execute(f"CREATE DATABASE {self.database_name};")
                    print(f"Database {self.database_name} created.")
                else:
                    print(f"Database {self.database_name} already exists.")
        finally:
            connection.close()

    def run_migrations(self):
        print("Running migrations...")
        migrator = MySQLMigrator(self.db)

        migrations_dir = os.path.join(project_root, 'src', 'migrations')
        migration_files = sorted(os.listdir(migrations_dir))

        applied_migrations = []

        for migration_file in migration_files:
            if migration_file.endswith('.py') and migration_file != '__init__.py':
                migration_name = migration_file[:-3]
                if migration_name not in applied_migrations:
                    migration_module_path = os.path.join('src', 'migrations', migration_name).replace(os.path.sep, '.')
                    print(f"Applying migration: {migration_name}")
                    migration_module = importlib.import_module(migration_module_path)
                    with self.db.atomic():
                        migration_module.migrate(migrator, self.db)
                        print(f"Migration {migration_name} applied successfully.")
                        applied_migrations.append(migration_name)
                else:
                    print(f"Migration {migration_name} already applied. Skipping.")

    def initialize_database(self):
        print("Initializing database...")
        self.db.connect()
        print("Database connected.")
        #self.run_migrations()
        from src.db.models.db_models import User, Payment, DBProxy, DBProxyHistory
        models = [User, Payment, DBProxy, DBProxyHistory]
        for model in models:
            model._meta.database = self.db  # Set the database attribute for each model
        self.db.create_tables(models)
        print(f"Tables created: {', '.join([model.__name__ for model in models])}")


    def close_database(self):
        self.db.close()
        print("Database connection closed.")

def main():
    secret_name = "rds!db-e7b062d9-309f-46cb-8728-7938882704a7"
    region_name = "us-east-1"
    database_name = "db_proxystore"
    database_host = "db-proxystore.cxeiek4muj6l.us-east-1.rds.amazonaws.com"

    database = Database(secret_name, region_name, database_name, database_host)
    database.create_database_if_not_exists()

    try:
        database.initialize_database()
        # Your main code logic goes here
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        database.close_database()

if __name__ == '__main__':
    main()