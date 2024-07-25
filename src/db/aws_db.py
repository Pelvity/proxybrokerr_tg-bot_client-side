import logging
import os
import sys
import io
import time
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sshtunnel import SSHTunnelForwarder
import paramiko
from src.bot.config import (
    DATABASE_TYPE, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST,
    SSH_HOST, SSH_PORT, SSH_USER, SSH_PKEY, USE_SSH, DB_PORT
)

logger = logging.getLogger(__name__)

# Define the base model for your database tables
Base = declarative_base()

class AWSRDSService:
    def __init__(self):
        logger.info("Initializing AWSRDSService.")
        self.engine = None
        self.Session = None
        self.tunnel = None
        self.last_activity = time.time()
        self.connection_string = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DB_PORT}/{DATABASE_NAME}"
        self.connect()

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
        logger.info("Establishing a new database connection.")
        try:
            self.validate_config()
            if USE_SSH:
                self.engine, self.tunnel = self.get_local_db_connection()
            else:
                self.engine, _ = self.get_ec2_db_connection()
            self.Session = scoped_session(sessionmaker(bind=self.engine))
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
        logger.info("Connecting to database through SSH tunnel.")
        try:
            ssh_tunnel = self.set_up_ssh_tunnel()
            ssh_tunnel.start()
            logger.info(f"SSH Tunnel established. Local port: {ssh_tunnel.local_bind_port}")

            db_url = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@127.0.0.1:{ssh_tunnel.local_bind_port}/{DATABASE_NAME}"
            engine = create_engine(db_url, poolclass=QueuePool, pool_size=1, max_overflow=3, pool_timeout=30)
            return engine, ssh_tunnel
        except Exception as e:
            logger.error(f"Failed to establish SSH tunnel: {str(e)}")
            raise

    def get_ec2_db_connection(self):
        logger.info("Connecting directly to the database.")
        engine = create_engine(self.connection_string, poolclass=QueuePool, pool_size=5, max_overflow=10, pool_timeout=30)
        return engine, None

    @contextmanager
    def get_session(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        logger.info("Creating database tables.")
        from src.db.models.db_models import Base
        Base.metadata.create_all(self.engine)

    def execute_query(self, query, params=None):
        logger.info(f"Executing query: {query}")
        with self.get_session() as session:
            session.execute(text(query), params)

    def fetch_data(self, query, params=None):
        logger.info(f"Fetching data with query: {query}")
        with self.get_session() as session:
            result = session.execute(text(query), params)
            return [dict(row) for row in result]

    def check_connection(self):
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            logger.error("Database connection check failed.")
            return False

    def close(self):
        logger.info("Closing database connection.")
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        if self.tunnel and self.tunnel.is_active:
            logger.info("Closing SSH tunnel.")
            self.tunnel.stop()

aws_rds_service = AWSRDSService()

def test_connection():
    try:
        if aws_rds_service.check_connection():
            logger.info("Successfully connected to the database.")
        else:
            logger.error("Failed to connect to the database.")
    except Exception as e:
        logger.error(f"An error occurred during connection test: {str(e)}")
    finally:
        aws_rds_service.close()

if __name__ == "__main__":
    test_connection()