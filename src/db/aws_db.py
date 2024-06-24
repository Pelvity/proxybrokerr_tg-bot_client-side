import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.bot.config import SQL_CONNECTIONSTRING

# Configure logging
logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine using the connection string
logger.info("Creating SQLAlchemy engine.")
#logging.info("SQL_CONNECTIONSTRING", SQL_CONNECTIONSTRING)
engine = create_engine(SQL_CONNECTIONSTRING)

# Create a session factory
Session = sessionmaker(bind=engine)

# Define the base model for your database tables
Base = declarative_base()

class AWSRDSService:
    def __init__(self, connection_string=SQL_CONNECTIONSTRING):
        logger.info("Initializing AWSRDSService.")
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def connect(self):
        """Establishes a new database session."""
        logger.info("Establishing a new database session.")
        return self.Session()

    def print_current_session(self):
        """Prints the identity key of the current session if available."""
        session = Session.object_session(self)
        if session is not None:
            logger.info(f"Current Session Identity Key: {session.identity_key}")
        else:
            logger.info("No active session found.")
            
    def create_tables(self):
        """Creates database tables if they don't exist."""
        logger.info("Creating database tables.")
        from src.db.models.db_models import Base  # Import Base here to avoid circular imports
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Provides a new database session."""
        logger.info("Getting a new database session.")
        return self.Session()

    def execute_query(self, query, params=None):
        """
        Executes a SQL query.

        Args:
            query (str): The SQL query to execute.
            params (dict, optional): Parameters to pass to the query. Defaults to None.
        """
        logger.info(f"Executing query: {query}")
        with self.connect() as session:
            session.execute(query, params)
            session.commit()

    def fetch_data(self, query, params=None):
        """
        Fetches data from the database.

        Args:
            query (str): The SQL query to execute.
            params (dict, optional): Parameters to pass to the query. Defaults to None.

        Returns:
            list: A list of dictionaries, each dictionary representing a row in the result set.
        """
        logger.info(f"Fetching data with query: {query}")
        with self.connect() as session:
            result = session.execute(query, params)
            return [dict(row) for row in result]

    def close(self):
        """Disposes of the database engine connection."""
        logger.info("Disposing of the database engine connection.")
        if self.engine:
            self.engine.dispose()
