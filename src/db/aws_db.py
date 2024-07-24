import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import io
import paramiko
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sshtunnel import SSHTunnelForwarder
from src.bot.config import (
    DATABASE_TYPE, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST,
    SSH_HOST, SSH_PORT, SSH_USER, SSH_PKEY, USE_SSH, DB_PORT
)

# Configure logging
logger = logging.getLogger(__name__)

# Define the base model for your database tables
Base = declarative_base()

class AWSRDSService:
    def __init__(self):
        logger.info("Initializing AWSRDSService.")
        self.engine = None
        self.Session = None
        self.tunnel = None
        self.connection_string = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DB_PORT}/{DATABASE_NAME}"

    def validate_config(self):
        required_configs = [DATABASE_TYPE, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DB_PORT]
        
        for config in required_configs:
            if not config:
                raise ValueError(f"Missing required configuration: {config}")

        if USE_SSH:
            ssh_configs = [SSH_HOST, SSH_PORT, SSH_USER, SSH_PKEY]
            for config in ssh_configs:
                if not config:
                    raise ValueError(f"SSH is enabled but missing required configuration: {config}")

    def connect(self):
        """Establishes a new database connection, using SSH if configured."""
        logger.info("Establishing a new database connection.")
        try:
            self.validate_config()
            if USE_SSH:
                self.engine, self.tunnel = self.get_local_db_connection()
            else:
                self.engine, _ = self.get_ec2_db_connection()
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            logger.error(f"Failed to connect to the database: {str(e)}")
            raise

    def set_up_ssh_tunnel(self):
        return SSHTunnelForwarder(
            (SSH_HOST, int(SSH_PORT)),
            ssh_username=SSH_USER,
            ssh_pkey=self._get_ssh_key(),
            remote_bind_address=(DATABASE_HOST, int(DB_PORT))
        )

    def _get_ssh_key(self):
        if os.path.isfile(SSH_PKEY):
            return SSH_PKEY
        else:
            return paramiko.RSAKey.from_private_key(io.StringIO(SSH_PKEY))

    def get_local_db_connection(self):
        """Establishes an SSH tunnel and creates a database connection through it."""
        logger.info("Connecting to database through SSH tunnel.")
        try:
            ssh_tunnel = self.set_up_ssh_tunnel()
            ssh_tunnel.start()
            logger.info(f"SSH Tunnel established. Local port: {ssh_tunnel.local_bind_port}")

            db_url = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@127.0.0.1:{ssh_tunnel.local_bind_port}/{DATABASE_NAME}"
            engine = create_engine(db_url)
            return engine, ssh_tunnel
        except Exception as e:
            logger.error(f"Failed to establish SSH tunnel: {str(e)}")
            raise

    def get_ec2_db_connection(self):
        """Creates a direct database connection without SSH."""
        logger.info("Connecting directly to the database.")
        engine = create_engine(self.connection_string)
        return engine, None

    def get_session(self):
        """Provides a new database session."""
        logger.info("Getting a new database session.")
        if not self.Session:
            self.connect()
        return self.Session()

    def print_current_session(self):
        """Prints the identity key of the current session if available."""
        session = self.get_session()
        if session is not None:
            logger.info(f"Current Session Identity Key: {session.identity_key}")
        else:
            logger.info("No active session found.")
            
    def create_tables(self):
        """Creates database tables if they don't exist."""
        logger.info("Creating database tables.")
        from src.db.models.db_models import Base  # Import Base here to avoid circular imports
        Base.metadata.create_all(self.engine)

    def execute_query(self, query, params=None):
        """
        Executes a SQL query.

        Args:
            query (str): The SQL query to execute.
            params (dict, optional): Parameters to pass to the query. Defaults to None.
        """
        logger.info(f"Executing query: {query}")
        with self.get_session() as session:
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
        with self.get_session() as session:
            result = session.execute(query, params)
            return [dict(row) for row in result]

    def close(self):
        """Disposes of the database engine connection and closes SSH tunnel if used."""
        logger.info("Closing database connection.")
        if self.engine:
            self.engine.dispose()
        if self.tunnel and self.tunnel.is_active:
            logger.info("Closing SSH tunnel.")
            self.tunnel.stop()

# Create a global instance of AWSRDSService
aws_rds_service = AWSRDSService()

# Test the database connection
def test_connection():
    try:
        aws_rds_service.connect()
        with aws_rds_service.get_session() as session:
            # Try a simple query
            result = session.execute(text("SELECT 1")).fetchone()
            logger.info(f"Successfully connected to the database. Result: {result[0]}")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
    finally:
        aws_rds_service.close()

if __name__ == "__main__":
    test_connection()