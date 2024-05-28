import requests
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List
import json
from peewee import IntegrityError
from time import time

from .proxyServiceInterface import ProxyServiceInterface
from ..bot.models.proxy_models import Proxy, ProxyConnection
from src.db.models.db_models import DBProxy, DBProxyConnection, User, UserType
from src.db.db_utils import *

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
load_dotenv(dotenv_path)

# Now you can access the environment variables
LOCALTONET_API_KEY = os.environ.get("LOCALTONET_API_KEY")

class LocaltonetManager(ProxyServiceInterface):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://localtonet.com/api"
        self.service_name = "ltn"

    async def getAllProxies(self) -> List[DBProxy]:
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = requests.get(f"{self.base_url}/GetTunnels", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data.get("hasError"):
                tunnels = data.get("result", [])
                connections = []
                now = datetime.now()
                for tunnel in tunnels:
                    expiration_date = self.getConnectionExpirationDate(tunnel['id'])
                    if expiration_date:
                        days_left = (expiration_date - now).days
                        hours_left = (expiration_date - now).seconds // 3600
                    else:
                        days_left = 0
                        hours_left = 0
                    name = tunnel.get('authenticationUsername') or 'N/A'
                    external_user_id = tunnel.get('externalUserId', 'N/A') or 'N/A'
                    user = external_user_id.split('---')[1] if '---' in external_user_id else 'N/A'
                    connection = DBProxy(
                        #id=tunnel['id'],
                        id=tunnel.get('id', ''),
                        name=name,
                        description=name,
                        authToken=tunnel.get('authToken', ''),
                        proxies=[],  # Fetch and add actual proxies if needed
                        user=user,
                        expiration_date=expiration_date,
                        days_left=days_left,
                        hours_left=hours_left,
                        tariff_plan="Unlimited",
                        tariff_expiration_date=datetime(3000,1,1),
                        tariff_days_left=None,
                        deviceModel=tunnel['authTokenName'],
                        active = True if tunnel.get('status') == 1 else False,
                        service_name='ltn'
                    )
                    connections.append(connection)
                # Sort connections by days left, if needed
                #connections.sort(key=lambda x: x.days_left, reverse=True)
                return connections
            else:
                return f"Error: {data.get('errors')}"
        else:
            return f"Failed to fetch tunnels: {response.status_code}"
        
    async def getTunnelsByAuthToken(self, authtoken):
        """
        Retrieves the list of tunnels associated with a specific authToken from LocalToneT.
        :param authtoken: The authToken to retrieve tunnels for.
        :return: The list of tunnels or an error message.
        """
        url = f"{self.base_url}/GetTunnelsByAuthToken/{authtoken}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data.get("hasError"):
                return data.get("result", [])
            else:
                return f"Error: {data.get('errors')}"
        else:
            return f"Failed to fetch tunnels by authToken: {response.status_code}"      
         
    def getConnectionExpirationDate(self, tunnel_id):
        """
        Retrieves the expiration date of a tunnel from LocalToneT by its ID.
        :param tunnel_id: The ID of the tunnel to retrieve the expiration date for.
        :return: The expiration date of the tunnel as a string without fractional seconds, or an error message.
        """
        url = f"{self.base_url}/GetExpirationDateByTunnelId/{tunnel_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data.get("hasError"):
                expiration_date_str = data.get("result", {}).get("expirationDate", None)
                if expiration_date_str:
                    # Parse the date string into a datetime object
                    #print(repr(expiration_date_str))
                    #print(len(expiration_date_str))
                    try:
                        # Trim the last character if the string length is 27
                        if len(expiration_date_str) == 27:
                            expiration_date_str = expiration_date_str[:-1]
                        expiration_date_obj = datetime.strptime(expiration_date_str, '%Y-%m-%d %H:%M:%S.%f')
                        #print(expiration_date_obj)
                    except ValueError as e:
                        print(f"Error parsing date: {e}")
                    #print(expiration_date_obj)
                    # Format the datetime object back into a string without fractional seconds
                    #formatted_expiration_date = expiration_date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    return expiration_date_obj
                else:
                    return None
            else:
                return f"Error: {data.get('errors')}"
        else:
            return f"Failed to fetch tunnel expiration date: {response.status_code}"
        
    async def getConnectionsOfProxy(self, authToken):
        """
        Fetches proxy details for a given authToken and returns a list of Proxy instances.
        """
        url = f"{self.base_url}/GetTunnelsByAuthToken/{authToken}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        response = requests.get(url, headers=headers)
        proxies = []  # Initialize an empty list to hold the Proxy instances

        if response.status_code == 200:
            data = response.json()
            if not data.get("hasError"):
                raw_proxies = data.get("result", [])
                for proxy in raw_proxies:
                    # Create a Proxy instance for each item in raw_proxies
                    proxy_instance = DBProxyConnection(
                        id=proxy['id'],
                        userId=proxy.get('userId', ''),
                        created_timestamp=proxy.get('createdTimestamp', 0),
                        updated_timestamp=proxy.get('updatedTimestamp', 0),
                        name=proxy.get('name', ''),
                        description=proxy.get('description', ''),
                        host=proxy.get('serverIp', ''),
                        port=proxy.get('serverPort', 0),
                        login=proxy.get('authenticationUsername', ''),  # Assuming this is the login
                        password=proxy.get('authenticationPassword', ''),  # Assuming this is the password
                        type=proxy.get('protocolType', ''),
                        connectionId=proxy.get('guidId', ''),  # Assuming this is the connection ID
                        active=proxy.get('status', False) == 1,  # Assuming status 1 means active
                        #deviceModel=proxy.get('authTokenName', '')
                    )
                    proxies.append(proxy_instance)
            else:
                print(f"Error: {data.get('errors')}")
        else:
            print(f"Failed to fetch tunnels by authToken: {response.status_code}")

        return proxies

    async def setExpirationDateForConnection(self, tunnelId: str, new_expirationDate: datetime) -> str:
        """
        Sets the expiration date for a specific tunnel and keeps track of the original expiration date.

        :param tunnelId: The ID of the tunnel to update.
        :param new_expirationDate: The new expiration date as a datetime object.
        :return: A message indicating the result of the operation.
        """
        # Convert the new expiration date to the API's expected date-time format
        #formatted_new_expirationDate = new_expirationDate.strftime('%Y-%m-%d %H:%M:%S')
        formatted_new_expirationDate = new_expirationDate.isoformat()

        # Fetch the current expiration date for comparison (implement this method)
        """ current_expiration_date = self.getConnectionExpirationDate(tunnelId)
        if current_expiration_date is None:
            return "Failed to fetch current expiration date."

        # Compare the current and new expiration dates
        if new_expirationDate <= current_expiration_date:
            return "The new expiration date must be later than the current expiration date." """

        # Proceed to update the expiration date
        url = f"{self.base_url}/SetExpirationDateForTunnel"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        payload = {
            "tunnelId": tunnelId,
            "expirationDate": formatted_new_expirationDate
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            data = response.json()
            if not data.get("hasError"):
                return "Expiration date updated successfully."
            else:
                error_messages = ', '.join(data.get("errors", ["Unknown error."]))
                return f"Error: {error_messages}"
        else:
            return f"Failed to set expiration date: HTTP {response.status_code}"
    
"""     async def sync_connections(self):
        proxies = await self.getAllProxies()
        for proxy in proxies:
            connections = await self.getConnectionsOfProxy(proxy.authToken)
            user, user_created = User.get_or_create(
                username=proxy.user.lstrip('@') if proxy.user else None,
                defaults={
                    'user_type': UserType.TELEGRAM.value,  # Assuming Telegram users by default
                    'first_name': getattr(proxy, 'first_name', None),
                    'last_name': getattr(proxy, 'last_name', None),
                    'joined_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'is_active': True
                }
            )

            try:
                db_proxy_defaults = {
                    'name': proxy.name,
                    'user': user,
                    'tariff_plan': proxy.tariff_plan,
                    'tariff_expiration_date': proxy.tariff_expiration_date.strftime("%Y-%m-%d %H:%M:%S"),
                    'days_left': proxy.days_left,
                    'hours_left': proxy.hours_left,
                    'device_model': proxy.deviceModel,
                    'active': proxy.active,
                    'service_name': 'ipr'  # or 'ipr' for iproxyService
                }

                if proxy.expiration_date is not None:
                    db_proxy_defaults['expiration_date'] = proxy.expiration_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    db_proxy_defaults['expiration_date'] = None

                db_proxy, created = Proxy.get_or_create(
                    auth_token=proxy.id,
                    defaults=db_proxy_defaults
                )

                if not created:
                    update_proxy_data(db_proxy, proxy, user)

                # Get the existing connections for the proxy from the database
                existing_connections = {connection.id: connection for connection in db_proxy.connections}

                # Create a set to store the IDs of connections retrieved from the API
                api_connection_ids = set()

                for connection in connections:
                    created_datetime = datetime.fromtimestamp(connection.created_timestamp/1000).strftime("%Y-%m-%d %H:%M:%S")
                    updated_datetime = datetime.fromtimestamp(connection.updated_timestamp/1000).strftime("%Y-%m-%d %H:%M:%S")

                    # Create or update the DBProxyConnection record
                    db_connection, connection_created = ProxyConnection.get_or_create(
                        id=connection.id,
                        defaults={
                            'user': user,
                            'proxy': db_proxy,
                            'created_timestamp': created_datetime,
                            'updated_timestamp': updated_datetime,
                            'name': connection.name,
                            'description': connection.description,
                            'host': getattr(connection, 'host', ''),
                            'port': getattr(connection, 'port', 0),
                            'login': getattr(connection, 'login', ''),
                            'password': getattr(connection, 'password', ''),
                            'connection_type': getattr(connection, 'type', ''),
                            'active': connection.active,
                            'deleted': False  # Set deleted to False for connections retrieved from the API
                        }
                    )
                    if not connection_created:
                        update_connection_data(db_connection, connection)
                        db_connection.deleted = False  # Set deleted to False for existing connections retrieved from the API
                        db_connection.save()

                    # Add the connection ID to the set of IDs retrieved from the API
                    api_connection_ids.add(connection.id)

                # Mark the connections that exist in the database but not in the API response as deleted
                for connection_id, db_connection in existing_connections.items():
                    if int(connection_id) not in api_connection_ids:
                        db_connection.deleted = True
                        db_connection.save()

            except IntegrityError as e:
                print(f"Failed to create or update DBProxy or DBProxyConnection due to IntegrityError: {e}")

 """



# Example usage:
def main():
    proxy_manager = LocaltonetManager(LOCALTONET_API_KEY)
    tunnels = proxy_manager.GetTunnels()
    expirationdate = proxy_manager.GetExpirationDateByTunnelId('298487')
    proxies = proxy_manager.getConnectionsOfProxy('t9FwScgExiAnZkPVraCHjGpvsXJu7Lyf1')
    print(tunnels)
    print(expirationdate)

if __name__ == "__main__":
    main()