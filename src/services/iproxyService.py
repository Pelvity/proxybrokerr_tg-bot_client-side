import logging
from venv import logger
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
import json
import aiohttp
import zipfile
import io
import pandas as pd
from aiohttp import ClientResponseError, ClientConnectorError, ClientPayloadError, ServerDisconnectedError, ClientTimeout
import asyncio
import os
from peewee import IntegrityError 
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError

from src.bot.config import IPROXY_API_KEY
from src.db.aws_db import AWSRDSService
from src.services.proxyServiceInterface import ProxyServiceInterface
from src.bot.models.proxy_models import Proxy, ProxyConnection
from src.db.models.db_models import (
    DBProxy,
    DBProxyConnection,
    ConnectionDataChange,
    UserConnectionChange,
    User,
    ChangeType,
    DBHost,
    UserConnectionChangeType,
)
from src.db.azure_db import AzureSQLService
from src.db.repositories.user_repositories import UserRepository 

#database_service = AzureSQLService() 
database_service = AWSRDSService() 

class IProxyManager(ProxyServiceInterface):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.iproxy.online/v1"
        self.service_name = "ipr"

    async def getAllProxies(self) -> List[Proxy]:
        headers = {'Authorization': self.api_key}
        response = requests.get(f"{self.base_url}/connections", headers=headers)
        result = response.json()["result"]
        user_connections = [conn for conn in result]

        now = datetime.now()
        connections = []
        for conn in user_connections:
            name_desc = conn['name']
            name_parts = name_desc.rsplit(' - ', 1)
            name = name_parts[0]
            date_str = name_parts[1] if len(name_parts) > 1 else None

            tariff_plan, tariff_expiration_str = conn['planDetails']['message'].split(' active till ')
            tariff_expiration_date = datetime.strptime(tariff_expiration_str, '%d.%m.%Y')
            
            if date_str:
                try:
                    expiration_date = datetime.strptime(date_str, '%d/%m/%Y')
                    days_left = (expiration_date - now).days
                    hours_left = (expiration_date - now).seconds // 3600
                except ValueError:
                    # If date parsing fails, set default values
                    expiration_date = None
                    days_left = 0
                    hours_left = 0
            else:
                expiration_date = None
                days_left = 0
                hours_left = 0

            tariff_days_left = (tariff_expiration_date - now + timedelta(days=1)).days

            connection = Proxy(
                id=conn['id'],
                name=name,
                authToken=conn.get('id', ''),
                proxies=[],
                user=conn.get('description', ''),
                description=conn.get('description', ''),
                expiration_date=expiration_date,
                days_left=days_left,
                hours_left=hours_left,
                tariff_plan=tariff_plan,
                tariff_expiration_date=tariff_expiration_date,
                tariff_days_left=tariff_days_left,
                deviceModel=conn.get('deviceModel', ''),
                active=conn.get('active', 0),
                service_name='ipr'
            )

            connections.append(connection)
        
        return connections

    async def getConnectionsOfProxy(self, connection_id) -> List[ProxyConnection]:
        headers = {'Authorization': self.api_key}
        response = requests.get(f"{self.base_url}/connections/{connection_id}/proxies", headers=headers)
        proxies = []
        if response.status_code == 200:
            data = json.loads(response.text).get("result", [])
            for item in data:
                proxy = ProxyConnection(
                    id=item.get('id'),
                    userId=item.get('userId'),
                    created_timestamp=item.get('createdTimestamp'),
                    updated_timestamp=item.get('updatedTimestamp'),
                    name=item.get('name'),
                    description=item.get('description'),
                    user=item.get('description'),
                    host=item.get('ip'),
                    port=item.get('port'),
                    login=item.get('login'),
                    password=item.get('password'),
                    type=item.get('type'),
                    connectionId=item.get('connectionId'),
                    active=item.get('active'),
                )
                proxies.append(proxy)
        else:
            logging.error(f"Failed to fetch proxies: {response.status_code}")
        return proxies

    async def sync_connections(self):
        try:
            api_proxies = await self.getAllProxies()

            with database_service.get_user_repository() as session:
                user_repository = UserRepository(session)

                db_proxies = session.query(DBProxy).all()
                db_proxy_ids = {proxy.id for proxy in db_proxies}
                api_proxy_ids = {proxy.id for proxy in api_proxies}

                self._process_deleted_proxies(session, db_proxy_ids, api_proxy_ids)

                for api_proxy in api_proxies:
                    user = user_repository.get_or_create_user_by_username(session, api_proxy.user)
                    if not user:
                        logging.warning(f"Skipping proxy {api_proxy.id} due to user resolution issue.")
                        continue

                    db_proxy = self._get_or_create_proxy(session, api_proxy, user)
                    api_connections = await self.getConnectionsOfProxy(api_proxy.authToken)
                    await self._sync_proxy_connections(session, db_proxy, api_connections, user_repository)

            session.commit()
        except SQLAlchemyIntegrityError as e:
            logging.error(f"IntegrityError while syncing connections: {e}")
            session.rollback()
        except Exception as e:
            logging.error(f"An error occurred while syncing connections: {e}")
            session.rollback()

    def _process_deleted_proxies(self, session: Session, db_proxy_ids, api_proxy_ids):
        deleted_proxy_ids = db_proxy_ids - api_proxy_ids
        for deleted_proxy_id in deleted_proxy_ids:
            db_proxy = session.query(DBProxy).filter_by(id=deleted_proxy_id).first()
            if db_proxy:
                db_proxy.active = False
                for db_connection in db_proxy.connections:
                    db_connection.deleted = True
                session.commit()

    def _get_or_create_proxy(self, session: Session, api_proxy, user: User):
        db_proxy = session.query(DBProxy).filter_by(id=api_proxy.id).first()
        if db_proxy is None:
            db_proxy = DBProxy(
                id=api_proxy.id,
                phone_id=None,
                name=api_proxy.name,
                tariff_plan=api_proxy.tariff_plan,
                tariff_expiration_date=api_proxy.tariff_expiration_date,
                device_model=api_proxy.deviceModel,
                active=api_proxy.active,
                service_name='ipr',
            )
            session.add(db_proxy)
            session.commit()
        else:
            self._update_proxy(db_proxy, api_proxy.__dict__, session)
        return db_proxy

    async def _sync_proxy_connections(self, session: Session, db_proxy: DBProxy, api_connections, user_repository: UserRepository):
        api_connection_ids = {api_connection.id for api_connection in api_connections}

        for api_connection in api_connections:
            created_datetime = datetime.fromtimestamp(api_connection.created_timestamp / 1000)
            updated_datetime = datetime.fromtimestamp(api_connection.updated_timestamp / 1000)
            user = user_repository.get_or_create_user_by_username(session, api_connection.user)

            # Get or create host
            host = self._get_or_create_host(session, api_connection.host)

            connection_data = {
                'id': api_connection.id,
                'proxy_id': db_proxy.id,
                'user_id': user.id if user else None,
                'host_id': host.id if host else None,
                'created_datetime': created_datetime,
                'updated_datetime': updated_datetime,
                'expiration_date': datetime.now() + timedelta(days=30),  # Assuming 30 days validity
                'name': api_connection.name,
                'description': api_connection.description,
                'port': getattr(api_connection, 'port', 0),
                'login': getattr(api_connection, 'login', ''),
                'password': getattr(api_connection, 'password', ''),
                'connection_type': getattr(api_connection, 'type', ''),
                'active': api_connection.active,
                'deleted': False,
            }

            db_connection = session.query(DBProxyConnection).filter_by(id=api_connection.id).first()

            if db_connection is None:
                db_connection = DBProxyConnection(**connection_data)
                session.add(db_connection)
                self._create_user_connection_change(session, db_connection, None, user, UserConnectionChangeType.ASSIGNED)
            else:
                if self._has_connection_data_changed(db_connection, connection_data):
                    self._create_connection_data_changes(session, db_connection, connection_data, user)
                    old_user_id = db_connection.user_id
                    for key, value in connection_data.items():
                        setattr(db_connection, key, value)
                    db_connection.updated_datetime = datetime.now(timezone.utc)
                    if old_user_id != user.id:
                        self._create_user_connection_change(session, db_connection, old_user_id, user, UserConnectionChangeType.REASSIGNED)

        self._handle_deleted_connections(session, db_proxy.id, api_connection_ids)

        session.commit()

    def _get_or_create_host(self, session: Session, host_ip: str) -> DBHost:
        host = session.query(DBHost).filter_by(host_ip=host_ip).first()
        if not host:
            host = DBHost(host_ip=host_ip, country_code='Unknown')  # You might want to add logic to determine the country code
            session.add(host)
            session.commit()
        return host

    def _has_connection_data_changed(self, db_connection: DBProxyConnection, connection_data):
        for attr in ['name', 'description', 'host_id', 'port', 'login', 'password', 'connection_type', 'user_id']:
            if getattr(db_connection, attr) != connection_data.get(attr):
                return True
        return False

    def _handle_deleted_connections(self, session: Session, proxy_id, api_connection_ids):
        deleted_connections = (
            session.query(DBProxyConnection)
            .filter(
                DBProxyConnection.proxy_id == proxy_id,
                DBProxyConnection.id.notin_(api_connection_ids),
            )
            .all()
        )
        for deleted_connection in deleted_connections:
            deleted_connection.deleted = True
            self._create_user_connection_change(session, deleted_connection, deleted_connection.user_id, None, UserConnectionChangeType.UNASSIGNED)
        session.commit()

    def _create_connection_data_changes(self, session: Session, db_connection: DBProxyConnection, new_data, change_by: User):
        changes = []
        for attr in ['name', 'description', 'host_id', 'port', 'login', 'password', 'connection_type', 'active']:
            old_value = getattr(db_connection, attr)
            new_value = new_data.get(attr)
            if old_value != new_value:
                changes.append(ConnectionDataChange(
                    connection_id=db_connection.id,
                    user_id=change_by.id if change_by else None,
                    change_type=ChangeType(attr),
                    old_value=str(old_value),
                    new_value=str(new_value),
                    change_date=datetime.now(timezone.utc),
                ))
        if changes:
            session.bulk_save_objects(changes)

    def _create_user_connection_change(self, session: Session, connection: DBProxyConnection, old_user_id: Optional[int], new_user: Optional[User], change_type: UserConnectionChangeType):
        change = UserConnectionChange(
            connection_id=connection.id,
            old_user_id=old_user_id,
            new_user_id=new_user.id if new_user else None,
            change_type=change_type,
            change_date=datetime.now(timezone.utc)
        )
        session.add(change)

    def _update_proxy(self, db_proxy: DBProxy, api_proxy_data: dict, session: Session):
        for key, value in api_proxy_data.items():
            if hasattr(db_proxy, key) and getattr(db_proxy, key) != value:
                setattr(db_proxy, key, value)
        session.commit()

def test_sync_connections():
    logger.info("start")
    iproxy_service = IProxyManager(IPROXY_API_KEY)
    iproxy_service.sync_connections()
    
if __name__ == "__main__":
    test_sync_connections()