from typing import List
from sqlalchemy import func
from datetime import datetime

from src.db.models.db_models import DBProxyConnection

class ConnectionRepository:
    def __init__(self, session):
        self.session = session

    def get_user_connections(self, user_id: int) -> List[DBProxyConnection]:
        """Retrieves connections associated with a user."""
        return self.session.query(DBProxyConnection).filter_by(user_id=user_id).all()

    def get_connection_by_id(self, connection_id: str) -> DBProxyConnection:
        """Retrieves a connection by its ID."""
        return self.session.query(DBProxyConnection).filter_by(id=connection_id).first()

    # Add other connection-related repository methods as needed 