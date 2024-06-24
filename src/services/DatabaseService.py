from abc import ABC, abstractmethod
import pymssql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bot.config import DATABASE_HOST, DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USERNAME, DATABASE_TYPE, SQL_CONNECTIONSTRING

class DatabaseService(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute_query(self, query, params=None):
        pass

    @abstractmethod
    def fetch_data(self, query, params=None):
        pass

    @abstractmethod
    def close(self):
        pass

""" class MySQLService(DatabaseService): """
    # ... MySQL connection logic using pymysql ...

class AzureSQLService(DatabaseService):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.engine = None
        self.Session = None

    def connect(self):
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)
        return self.Session()

    def execute_query(self, query, params=None):
        with self.connect() as session:
            session.execute(query, params)
            session.commit()

    def fetch_data(self, query, params=None):
        with self.connect() as session:
            results = session.execute(query, params)
            return [dict(row) for row in results]  # Convert to dictionaries

    def close(self):
        if self.engine:
            self.engine.dispose()

def create_database_service(db_type, connection_string=None):
    if db_type == 'mysql':
        #return MySQLService(DATABASE_NAME, DATABASE_HOST, DATABASE_USERNAME, DATABASE_PASSWORD)
        pass
    elif db_type == 'azure':
        return AzureSQLService(connection_string or SQL_CONNECTIONSTRING)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

# Example usage in bot_setup.py
database = create_database_service(DATABASE_TYPE)

# ... rest of your bot setup ...