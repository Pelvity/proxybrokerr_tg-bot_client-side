from typing import Tuple
class ProxyServiceInterface:
    def getAllProxies(self):
        raise NotImplementedError

    def getProxyExpirationDate(self, connection_id):
        raise NotImplementedError
    
    def getConnectionsOfProxy(self, connection_id):
        raise NotImplementedError
    
    def updateProxyUser(self, connection_id, user):
        raise NotImplementedError
    
    def setExpirationDateForConnection(self, connection_id, expirationDate):
        raise NotImplementedError
    
    async def getTrafficData(self, connection_id: str, from_timestamp: int, to_timestamp: int) -> Tuple[int, int, str, bytes]:
        raise NotImplementedError


    # Add other common methods that proxy services should have