from typing import List, Optional
from sqlalchemy.orm import joinedload
from src.db.models.db_models import DBProxyConnection

class ConnectionRepository:
    def __init__(self, session):
        self.session = session

    def get_user_connections(self, user_id: int, include_deleted: bool = False) -> List[DBProxyConnection]:
        """Retrieves connections associated with a user.

        Args:
            user_id (int): The ID of the user.
            include_deleted (bool): If True, include deleted connections. Default is False.

        Returns:
            List[DBProxyConnection]: A list of connections associated with the user.
        """
        query = self.session.query(DBProxyConnection).options(joinedload(DBProxyConnection.proxy)).filter_by(user_id=user_id)
        
        if not include_deleted:
            query = query.filter_by(deleted=False)
        
        return query.all()

    def get_connection_by_id(self, connection_id: str) -> Optional[dict]:
        """Retrieves a connection by its ID and returns it as a dictionary."""
        connection = self.session.query(DBProxyConnection).filter_by(id=connection_id).first()
        return connection.to_dict() if connection else None
