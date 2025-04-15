from typing import List
from sqlalchemy import func
from datetime import datetime

from src.db.models.db_models import DBProxy, User

class ProxyRepository:
    def __init__(self, session):
        self.session = session

    def get_user_proxies(self, user_id: int) -> List[DBProxy]:
        """Retrieves proxies associated with a user, including days left."""
        proxies = (
            self.session.query(DBProxy)
            .filter(DBProxy.id == user_id)
            .all()
        )
        for proxy in proxies:
            proxy.days_left = (proxy.expiration_date - datetime.now()).days 
        return proxies