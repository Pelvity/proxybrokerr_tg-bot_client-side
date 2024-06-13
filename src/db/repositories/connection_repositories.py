from typing import List, Optional
from sqlalchemy.orm import joinedload
from src.db.models.db_models import DBProxyConnection

class ConnectionRepository:
    def __init__(self, session):
        self.session = session

    def get_user_connections(self, user_id: int) -> List[DBProxyConnection]:
        """Retrieves connections associated with a user."""
        return (
            self.session.query(DBProxyConnection)
            .options(joinedload(DBProxyConnection.proxy))
            .filter_by(user_id=user_id)
            .all()
        )

    def get_connection_by_id(self, connection_id: str) -> Optional[DBProxyConnection]:
        """Retrieves a connection by its ID."""
        return self.session.query(DBProxyConnection).filter_by(id=connection_id).first()
