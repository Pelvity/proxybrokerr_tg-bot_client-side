import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
import json
import aiohttp
import zipfile
import io
import pandas as pd
from aiohttp import ClientResponseError, ClientConnectorError, ClientPayloadError, ServerDisconnectedError, ClientTimeout
import asyncio
import os
from peewee import IntegrityError 
from typing import Optional

#from src.db.models.db_models import Proxy, ProxyHistory, User, ProxyConnection, UserType
from src.services.proxyServiceInterface import ProxyServiceInterface
from src.bot.models.proxy_models import Proxy, ProxyConnection
from src.db.models.db_models import ConnectionHistory, User,UserType, DBProxy, DBProxyConnection
from src.db.db_utils import update_connection, update_proxy
from src.db.azure_db import AzureSQLService
from src.db.repositories.user_repositories import UserRepository 

database_service = AzureSQLService() 

class IProxyManager(ProxyServiceInterface):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.iproxy.online/v1"
        self.service_name = "ipr"
        #self.user_repository = UserRepository(self.session) 

    async def getAllProxies(self) -> List[Proxy]:
        headers = {'Authorization': self.api_key}
        response = requests.get(f"{self.base_url}/connections", headers=headers)
        result = response.json()["result"]
        user_connections = [conn for conn in result]

        connection_names = [conn['name'] for conn in user_connections]
        if not connection_names:
            return []

        now = datetime.now()
        connections = []
        for name_desc, conn in zip(connection_names, user_connections):
            name, date_str = name_desc.split(' - ')
            tariff_plan, tariff_expiration_str = conn['planDetails']['message'].split(' active till ')
            tariff_expiration_date = datetime.strptime(tariff_expiration_str, '%d.%m.%Y')
            expiration_date = datetime.strptime(date_str, '%d/%m/%Y')
            days_left = (expiration_date - now).days
            tariff_days_left = (tariff_expiration_date - now + timedelta(days=1)).days
            hours_left = (expiration_date - now).seconds // 3600
            connection = Proxy(
                id=conn['id'],
                name=name,
                authToken=conn.get('id', ''),  # Use empty string as default if 'id' is missing
                proxies=[],  # Fetch and add actual proxies if needed
                user=conn.get('description', ''),  # Use empty string as default if 'description' is missing
                description=conn.get('description', ''),  # Use empty string as default if 'description' is missing
                #user_id = user_id,
                expiration_date=expiration_date or None,  # Use None as default if expiration_date is not available
                days_left=days_left or 0,  # Use 0 as default if days_left is not available
                hours_left=hours_left or 0,  # Use 0 as default if hours_left is not available
                tariff_plan=tariff_plan or '',  # Use empty string as default if tariff_plan is not available
                tariff_expiration_date=tariff_expiration_date or None,  # Use None as default if tariff_expiration_date is not available
                tariff_days_left=tariff_days_left or 0,  # Use 0 as default if tariff_days_left is not available
                deviceModel=conn.get('deviceModel', ''),  # Use empty string as default if 'deviceModel' is missing
                active=conn.get('active', 0),  # Use 0 as default if 'active' is missing
                service_name='ipr'
            )

            connections.append(connection)

        # Sort connections by days left, if needed
        #connections.sort(key=lambda x: x.days_left, reverse=True)
        
        return connections


    def getProxyExpirationDate(self, connection_id):
        # Implement logic to fetch expiration date for a given connection_id
        pass

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
            # Handle errors appropriately
            print(f"Failed to fetch proxies: {response.status_code}")
        return proxies
    
    async def updateConnectionName(self, connection_id, new_name):
        """
        Updates the name of a proxy connection.
        
        :param connection_id: The ID of the connection to update.
        :param new_name: The new name for the connection.
        :return: A success message or an error message.
        """
        url = f"{self.base_url}/connections/{connection_id}"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/merge-patch+json'
        }
        data = {'name': new_name}
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return "Connection name updated successfully."
        else:
            return f"Failed to update connection name: {response.status_code} - {response.text}"

    async def setExpirationDateForConnection(self, connection_id, new_expiration_date):
        """
        Sets the expiration date for a connection and updates its name accordingly.
        
        :param connection_id: The ID of the connection to update.
        :param new_expiration_date: The new expiration date for the connection, as a datetime object.
        :return: A success message or an error message.
        """
        # Fetch the list of proxies for the connection
        proxies_list = await self.getConnectionsOfProxy(connection_id)
        if not proxies_list:
            return "Failed to fetch connection info."

        # Find the proxy that matches the connection_id
        connection_details = next((proxy for proxy in proxies_list if proxy.connectionId == connection_id), None)
        if not connection_details:
            return "Connection details not found."

        # Split the existing name by ' - ' to examine the parts
        parts = connection_details.name.split(' - ')
        
        # If there are exactly 2 parts, it's assumed to be "Name - Date"
        # If there are more than 2 parts, it's assumed to be "Name - Date - SomeOtherInfo"
        # In both cases, we update the second part with the new expiration date.
        if len(parts) >= 2:
            parts[1] = new_expiration_date.strftime('%d/%m/%Y')
            # If there were more than 3 parts, we only keep the first 2 (Name and NewDate)
            new_name = ' - '.join(parts[:2])
        else:
            # If the name doesn't follow the expected format, return an error or handle accordingly
            return "Unexpected name format. Unable to update expiration date."

        # Update the connection name with the new expiration date
        return await self.updateConnectionName(connection_id, new_name)
              
    async def setTariffPlan(self, connection_id, tariff_id):
        url = f"https://iproxy.online/api-rt/phone/{connection_id}/change-plan/{tariff_id}?token=r:314235bd45a0995c6f2340c1b4df7b3e"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "sec-ch-ua": "\"Brave\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                return await response.json()

    async def update_tariffs_to_big_daddy_pro(self):
        logging.info("Starting the update_tariffs_to_big_daddy_pro method.")
        try:
            connections = await self.getAllProxies()
            if connections:
                logging.info(f"Found {len(connections)} connections to check for tariff updates.")
            else:
                logging.info("No connections found to update.")
            for conn in connections:
                logging.info(f"Checking tariff for connection: {conn.name}")
                # Proceed with the update only if the tariff days left are 0 or less
                if conn.tariff_days_left <= 0:
                    logging.info(f"Tariff days left for {conn.name} are 0 or less. Proceeding with tariff update.")
                    # First, update the tariff to 'Big Daddy' if it's not already
                    if conn.tariff_plan != 'BigDaddy':
                        logging.info(f"Updating tariff for {conn.name} to 'Big Daddy'.")
                        response = await self.setTariffPlan(conn.id, 'M7Fq2RKexi')  # 'M7Fq2RKexi' is the ID for 'Big Daddy'
                        if 'result' in response:
                            logging.info(f"Successfully updated tariff for {conn.name} to 'Big Daddy'. Now updating to 'Big Daddy Pro'.")
                        else:
                            logging.error(f"Failed to update tariff for {conn.name} to 'Big Daddy'. Error: {response.get('message', 'Unknown error')}")
                            continue  # Skip to the next connection if the update fails

                    # Then, update the tariff to 'Big Daddy Pro'
                    logging.info(f"Updating tariff for {conn.name} to 'Big Daddy Pro'.")
                    response = await self.setTariffPlan(conn.id, 'BNyW1yBaln')  # Assuming 'BNyW1yBaln' is the ID for 'Big Daddy Pro'
                    if 'result' in response:
                        logging.info(f"Successfully updated tariff for {conn.name} to 'Big Daddy Pro'.")
                    else:
                        logging.error(f"Failed to update tariff for {conn.name} to 'Big Daddy Pro'. Error: {response.get('message', 'Unknown error')}")
                else:
                    logging.info(f"No update needed for {conn.name}. Tariff days are sufficient.")
        except Exception as e:
            logging.error(f"An error occurred during the tariff update process: {str(e)}")

    async def getTrafficData(self, connection_id: str, from_timestamp: int, to_timestamp: int) -> Tuple[int, int, str, str]:
        url = f"https://iproxy.online/api-rt/phone/{connection_id}/logs-csv?from={from_timestamp}&to={to_timestamp}&name={connection_id}-{from_timestamp}_{to_timestamp}-logs.csv&&token=r:d5686a473a462e5aec393cdc7386033c"
        
        max_retries = 3
        retry_delay = 1
        timeout = 10
        
        zip_directory = "zip_files"
        os.makedirs(zip_directory, exist_ok=True)  # Create the directory if it doesn't exist
        
        zip_filename = f"{connection_id}-{from_timestamp}_{to_timestamp}-logs.zip"
        zip_file_path = os.path.join(zip_directory, zip_filename)
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=timeout) as response:
                        if response.status != 200:
                            error_message = f"Error fetching traffic data for connection {connection_id}. Status code: {response.status}"
                            logging.error(error_message)
                            return 0, 0, "N/A", "", error_message
                        
                        zip_data = await response.read()
                
                # Save the zip file to the specified directory
                with open(zip_file_path, "wb") as file:
                    file.write(zip_data)
                
                # Open the zip file from the saved location
                with zipfile.ZipFile(zip_file_path, "r") as zip_file:
                    csv_filename = zip_file.namelist()[0]
                    with zip_file.open(csv_filename) as csv_file:
                        
                        # Read the CSV file into a Pandas DataFrame
                        data = pd.read_csv(csv_file)
                        
                        if data.empty:
                            logging.warning(f"CSV data is empty for connection {connection_id} from {from_timestamp} to {to_timestamp}")
                            return 0, 0, "N/A", "", None
                        
                        total_tx_bytes = data['TxBytes'].sum()
                        total_rx_bytes = data['RxBytes'].sum()
                        
                        if 'ReqHost' in data.columns and data['ReqHost'].notnull().any():
                            most_used_service = data['ReqHost'].value_counts().idxmax()
                        else:
                            most_used_service = "N/A"
                        
                        # Seek back to the beginning of the file to read its contents into csv_data
                        csv_file.seek(0)
                        csv_data = csv_file.read().decode('utf-8')

                        return total_tx_bytes, total_rx_bytes, most_used_service, csv_data, None

            
            except (ClientResponseError, ClientConnectorError, ClientPayloadError, ServerDisconnectedError, zipfile.BadZipFile, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Error fetching traffic data for connection {connection_id}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    error_message = f"Failed to fetch traffic data for connection {connection_id} after {max_retries} attempts. Error: {str(e)}"
                    logging.error(error_message)
                    return 0, 0, "N/A", "", error_message

    async def sync_connections(self):
        """Synchronizes proxy connections from the IProxy API."""
        try:
            api_proxies = await self.getAllProxies()

            with database_service.get_session() as session:
                user_repository = UserRepository(session)
                for api_proxy in api_proxies:
                    user = await self._get_or_create_user_from_proxy(session, user_repository, api_proxy)
                    if user is None: 
                        print(f"Skipping proxy {api_proxy.id} due to user resolution issue.")
                        continue

                    db_proxy = self._get_or_create_proxy(session, api_proxy, user)
                    api_connections = await self.getConnectionsOfProxy(api_proxy.authToken)
                    #self._sync_proxy_connections(session, db_proxy, api_connections, user_repository)  # Pass user_repository here
                    await self._sync_proxy_connections(
                        session, db_proxy, api_connections, user_repository
                    )  # Call the function

        except IntegrityError as e:
            print(
                f"Failed to create or update DBProxy or DBProxyConnection due to IntegrityError: {e}"
            )
        except Exception as e:
            print(f"An error occurred while syncing connections: {e}")
    
    async def _get_or_create_user_from_proxy(self, session, user_repository, api_proxy) -> Optional[User]:
        """Fetches or creates a user based on API proxy data (username only)."""
        user = user_repository.get_or_create_user_by_username(session, api_proxy.user) 
        return user
    
    def _get_or_create_proxy(self, session, api_proxy, user):
        """Gets or creates a DBProxy based on the API proxy data."""
        db_proxy = session.query(DBProxy).filter_by(id=api_proxy.id).first()
        if db_proxy is None:
            db_proxy = DBProxy(
                id=api_proxy.id,
                phone_id=None,  
                name=api_proxy.name,
                # user_id=user.id,  # REMOVE THIS LINE - no longer in DBProxy
                expiration_date=api_proxy.expiration_date,
                #hours_left=api_proxy.hours_left,
                tariff_plan=api_proxy.tariff_plan,
                tariff_expiration_date=api_proxy.tariff_expiration_date,
                tariff_days_left=api_proxy.tariff_days_left,
                device_model=api_proxy.deviceModel,
                active=api_proxy.active,
                service_name='ipr',
            )
            session.add(db_proxy)
            session.commit()
        else:
            update_proxy(db_proxy, api_proxy.__dict__, session)
        return db_proxy
    
    async def _sync_proxy_connections(self, session, db_proxy, api_connections, user_repository):
        """Synchronizes DBProxyConnection records - handles user association."""
        api_connection_ids = {api_connection.id for api_connection in api_connections}

        for api_connection in api_connections:
            created_datetime = datetime.fromtimestamp(api_connection.created_timestamp / 1000)
            user = user_repository.get_or_create_user_by_username(session, api_connection.user)

            connection_data = { 
                'id': api_connection.id,
                'proxy_id': db_proxy.id,
                'user_id': user.id if user else None,
                'created_timestamp': created_datetime,
                'name': api_connection.name,
                'description': api_connection.description,
                'host': getattr(api_connection, 'host', ''),
                'port': getattr(api_connection, 'port', 0),
                'login': getattr(api_connection, 'login', ''),
                'password': getattr(api_connection, 'password', ''),
                'connection_type': getattr(api_connection, 'type', ''),
                'active': api_connection.active,
                'deleted': False,
            }

            db_connection = session.query(DBProxyConnection).filter_by(id=api_connection.id).first()

            if db_connection is None:
                # New connection, create history entry
                db_connection = DBProxyConnection(**connection_data)
                session.add(db_connection)
                self._create_connection_history(session, db_connection) 
            else:
                if self._has_connection_data_changed(db_connection, connection_data):
                    # Connection data changed, create history entry
                    self._create_connection_history(session, db_connection)
                    # Update connection data
                    for key, value in connection_data.items():
                        setattr(db_connection, key, value)
                    db_connection.updated_timestamp = datetime.now(timezone.utc)

        # Mark connections as deleted if not found in the API data 
        deleted_connections = (
            session.query(DBProxyConnection)
            .filter(
                DBProxyConnection.proxy_id == db_proxy.id,
                DBProxyConnection.id.notin_(api_connection_ids),
            )
            .all()
        )
        for deleted_connection in deleted_connections:
            self._create_connection_history(session, deleted_connection)
            deleted_connection.deleted = True 

        session.commit()

    def _has_connection_data_changed(self, db_connection, connection_data):
        """Check if relevant connection data has changed."""
        for attr in [
            'name', 'description', 'host', 'port', 'login', 'password', 
            'connection_type', 'user_id'
        ]:
            if getattr(db_connection, attr) != connection_data.get(attr):
                return True
        return False

    def _create_connection_history(self, session, db_connection):
        """Create a new connection history entry."""
        new_history = ConnectionHistory(
            connection_id=db_connection.id,
            user_id=db_connection.user_id,  # Store user_id in history
            name=db_connection.name,
            description=db_connection.description,
            host=db_connection.host,
            port=db_connection.port,
            login=db_connection.login,
            password=db_connection.password,
            connection_type=db_connection.connection_type,
            active = db_connection.active,
        )
        session.add(new_history)