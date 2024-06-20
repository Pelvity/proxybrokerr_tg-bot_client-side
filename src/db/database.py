# import pymysql
# from peewee import *
# import boto3
# from botocore.exceptions import ClientError
# import json
# import sys
# import os
# import base64
# from playhouse.migrate import *
# import importlib
# import pyodbc
# import pymssql

# from src.bot.config import DATABASE_HOST, DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USERNAME, DATABASE_TYPE, AZURE_SQL_CONNECTIONSTRING

# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# sys.path.append(project_root)

# # Create a DatabaseProxy for dynamic database switching
# db = DatabaseProxy()

# class Database:
#     def __init__(self, database_name, database_host, username=None, password=None, secret_name=None, region_name=None, database_type='mysql'):
#         self.database_name = database_name
#         self.database_host = database_host
#         self.username = username
#         self.password = password
#         self.secret_name = secret_name
#         self.region_name = region_name
#         self.database_type = database_type.lower()
#         self.secrets = self.get_secret() if secret_name else None

#         # 1. Connect to the database and initialize the DatabaseProxy first
#         self.connect_to_database()

#         # 2. Now that the database is connected, import and initialize the models
#         from src.db.models.db_models import User, Payment, DBProxy, ProxyHistory, DBProxyConnection, UserPhoneNumber
#         self.initialize_models([User, Payment, DBProxy, ProxyHistory, DBProxyConnection, UserPhoneNumber])

#     def connect_to_database(self):
#         # Create the database if it doesn't exist
#         self.create_database_if_not_exists()

#         if self.database_type == 'mysql':
#             db.initialize(MySQLDatabase(
#                 self.database_name,
#                 user=self.username,
#                 password=self.password,
#                 host=self.database_host,
#                 port=3306
#             ))
#         elif self.database_type == 'azure':
#             # Create a Peewee database object using the pymssql connection:
#             from playhouse.db_url import connect # Import connect from peewee

#             #azure_db = connect(f'mssql+pymssql://{self.username}:{self.password}@{self.database_host}:1433/{self.database_name}')
#             azure_db = connect(str(AZURE_SQL_CONNECTIONSTRING))
#             db.initialize(azure_db)  # Initialize the DatabaseProxy
#         else:
#             raise ValueError(f"Invalid database type: {self.database_type}")

#     def initialize_models(self, models):
#         # Create tables if they don't exist
#         db.create_tables(models, safe=True)

#         # Run migrations if needed
#         # self.run_migrations()

#     def get_secret(self):
#         if not self.secret_name or not self.region_name:
#             return None

#         session = boto3.session.Session()
#         client = session.client(service_name='secretsmanager', region_name=self.region_name)
#         try:
#             get_secret_value_response = client.get_secret_value(SecretId=self.secret_name)
#             print("Successfully retrieved secret from AWS Secrets Manager.")
#         except ClientError as e:
#             print(f"Failed to retrieve secret: {e}")
#             raise e
#         else:
#             if 'SecretString' in get_secret_value_response:
#                 return json.loads(get_secret_value_response['SecretString'])
#             else:
#                 decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
#                 return json.loads(decoded_binary_secret)

#     def configure_database(self):
#         if self.secrets:
#             username = self.secrets['username']
#             password = self.secrets['password']
#         else:
#             username = self.username
#             password = self.password

#         if self.database_type == 'mysql':
#             return MySQLDatabase(
#                 self.database_name,
#                 user=username,
#                 password=password,
#                 host=self.database_host,
#                 port=3306
#             )
#         elif self.database_type == 'azure':
#             conn_str = AZURE_SQL_CONNECTIONSTRING 
#             # Connect to Azure SQL Database and return the connection
#             return pyodbc.connect(conn_str)  
#         else:
#             raise ValueError(f"Invalid database type: {self.database_type}") 

#     def create_database_if_not_exists(self):
#         if self.database_type == 'mysql':
#             if self.secrets:
#                 username = self.secrets['username']
#                 password = self.secrets['password']
#             else:
#                 username = self.username
#                 password = self.password

#             connection = pymysql.connect(
#                 host=self.database_host,
#                 user=username,
#                 password=password,
#                 charset='utf8mb4',
#                 cursorclass=pymysql.cursors.DictCursor
#             )

#             try:
#                 with connection.cursor() as cursor:
#                     cursor.execute(f"SHOW DATABASES LIKE '{self.database_name}';")
#                     result = cursor.fetchone()
#                     if not result:
#                         cursor.execute(f"CREATE DATABASE {self.database_name};")
#                         print(f"Database {self.database_name} created.")
#                     else:
#                         print(f"Database {self.database_name} already exists.")
#             finally:
#                 connection.close()

#         elif self.database_type == 'azure':
#             # Database creation in Azure SQL Database is typically handled through the Azure portal
#             print("Database creation for Azure SQL Database should be handled through the Azure portal.")

#     def run_migrations(self, migration_names=None):
#         print("Running migrations...")
        
#         if self.database_type == 'mysql':
#             migrator = MySQLMigrator(self.db)

#             migrations_dir = os.path.join(project_root, 'src', 'migrations')
#             migration_files = sorted(os.listdir(migrations_dir))

#             applied_migrations = []

#             for migration_file in migration_files:
#                 if migration_file.endswith('.py') and migration_file != '__init__.py':
#                     migration_name = migration_file[:-3]
#                     if migration_names is None or migration_name in migration_names:
#                         if migration_name not in applied_migrations:
#                             migration_module_path = os.path.join('src', 'migrations', migration_name).replace(os.path.sep, '.')
#                             print(f"Applying migration: {migration_name}")
#                             migration_module = importlib.import_module(migration_module_path)
#                             with self.db.atomic():
#                                 migration_module.migrate(migrator, self.db)
#                                 print(f"Migration {migration_name} applied successfully.")
#                                 applied_migrations.append(migration_name)
#                         else:
#                             print(f"Migration {migration_name} already applied. Skipping.")
#                     else:
#                         print(f"Migration {migration_name} not selected. Skipping.")

#         elif self.database_type == 'azure':
#             # Handle Azure SQL migrations (potentially using a different library)
#             print("Migrations for Azure SQL Database are not currently implemented in this code.")

#     def initialize_database(self):
#         print("Initializing database...")
#         #self.db.connect()
#         print("Database connected.")
#         selected_migrations = ['0003_add_user_identity_columns', '0004_add_user_id_column']
#         #self.run_migrations(migration_names=selected_migrations)
#         from src.db.models.db_models import User, Payment, DBProxy, ProxyHistory, DBProxyConnection, UserPhoneNumber
#         models = [User, Payment, DBProxy, ProxyHistory, DBProxyConnection, UserPhoneNumber]
#         if self.database_type == 'mysql':
#             for model in models:
#                 model._meta.database = self.db  # Set the database attribute for each model
#             self.db.create_tables(models)
#             print(f"Tables created: {', '.join([model.__name__ for model in models])}")
#         elif self.database_type == 'azure':
#             # Implement table creation logic for Azure SQL Database
#             cursor = self.db.cursor()  # Assuming self.db is a pyodbc connection
#             # Example - Creating a simple table:
#             cursor.execute("""
#                 CREATE TABLE Users (
#                     Id INT IDENTITY(1,1) PRIMARY KEY,
#                     Name VARCHAR(255) NOT NULL
#                 )
#             """)
#             self.db.commit()
#             print("Table 'Users' created in Azure SQL Database.")

#     def close_database(self):
#         if self.database_type == 'mysql':
#             self.db.close()
#             print("Database connection closed.")
#         elif self.database_type == 'azure':
#             self.db.close() # Assuming self.db is a pyodbc connection
#             print("Azure SQL Database connection closed.")
            
            
# def main():
#     secret_name = "rds!db-e7b062d9-309f-46cb-8728-7938882704a7"
#     region_name = "us-east-1"
#     database_name = "db_proxystore"
#     database_host = "db-proxystore.cxeiek4muj6l.us-east-1.rds.amazonaws.com"

#     database = Database(DATABASE_NAME, DATABASE_HOST,DATABASE_USERNAME,DATABASE_PASSWORD)
#     database.create_database_if_not_exists()

#     try:
#         database.initialize_database()
#         # Your main code logic goes here
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#     finally:
#         database.close_database()

# if __name__ == '__main__':
#     main()