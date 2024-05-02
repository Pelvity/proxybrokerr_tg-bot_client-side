import requests
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List
import json

from .proxyServiceInterface import ProxyServiceInterface
from ..bot.models.proxy_models import Proxy, ProxyConnection
from src.db.models.db_models import DBProxyHistory, DBProxy, DBProxyConnection, User
from peewee import IntegrityError

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
load_dotenv(dotenv_path)

# Now you can access the environment variables
LOCALTONET_API_KEY = os.environ.get("LOCALTONET_API_KEY")

class LocaltonetManager(ProxyServiceInterface):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://localtonet.com/api"
        self.service_name = "ltn"

    async def getConnections(self) -> List[Proxy]:
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
                    connection = Proxy(
                        #id=tunnel['id'],
                        id=tunnel.get('id', ''),
                        name=name,
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
        
    async def getProxiesforConnection(self, authToken):
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
                    proxy_instance = ProxyConnection(
                        id=proxy['id'],
                        userId=proxy.get('userId', ''),
                        createdTimestamp=proxy.get('createdTimestamp', 0),
                        updatedTimestamp=proxy.get('updatedTimestamp', 0),
                        name=proxy.get('name', ''),
                        description=proxy.get('description', ''),
                        ip=proxy.get('serverIp', ''),
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
    
    async def sync_connections(self):
        connections = await self.getConnections()
        for connection in connections:
            user, user_created = User.get_or_create(
                username = connection.user.lstrip('@') if connection.user else None,
                defaults = {
                    'first_name': getattr(connection, 'first_name', None),  # Use None if 'first_name' is not available
                    'last_name': getattr(connection, 'last_name', None),
                    'joined_at': datetime.now(),  # Use the current time as the join date if not provided
                    'is_active': True  # Default to True if not specified
                }
            )

            try:
                proxy, created = DBProxy.get_or_create(
                    auth_token=connection.id,  # Assuming auth_token is unique
                    defaults={
                        'name': connection.name,
                        'user': user.id,  # Link to the user record
                        'expiration_date': connection.expiration_date,
                        'tariff_plan': connection.tariff_plan,
                        'tariff_expiration_date': connection.tariff_expiration_date,
                        'days_left': connection.days_left,
                        'hours_left': connection.hours_left,
                        'device_model': connection.deviceModel,
                        'active': connection.active,
                        'service_name': 'ltn'
                    }
                )
                if not created:
                    update_proxy_data(proxy, connection, user)
            except IntegrityError as e:
                print(f"Failed to create or update DBProxy due to IntegrityError: {e}")

def update_proxy_data(proxy, connection, user):
    # Save the old data in history before updating
    DBProxyHistory.create(
        proxy=proxy,
        user=user,  # Link to the user
        service_name=proxy.service_name,
        connection_id=proxy.id,
        name=proxy.name,
        expiration_date=proxy.expiration_date,
        tariff_plan=proxy.tariff_plan,
        tariff_expiration_date=proxy.tariff_expiration_date,
        created_at=proxy.created_at,
        updated_at=datetime.now()
    )
    # Update the proxy with new data
    proxy.name = connection.name
    proxy.expiration_date = connection.expiration_date
    proxy.tariff_plan = connection.tariff_plan
    proxy.tariff_expiration_date = connection.tariff_expiration_date
    proxy.updated_at = datetime.now()
    proxy.save()

# Example usage:
def main():
    proxy_manager = LocaltonetManager(LOCALTONET_API_KEY)
    tunnels = proxy_manager.GetTunnels()
    expirationdate = proxy_manager.GetExpirationDateByTunnelId('298487')
    proxies = proxy_manager.getProxiesforConnection('t9FwScgExiAnZkPVraCHjGpvsXJu7Lyf1')
    print(tunnels)
    print(expirationdate)

if __name__ == "__main__":
    main()