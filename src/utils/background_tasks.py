import asyncio
from src.services.iproxyService import IProxyManager
from src.services.localtonetService import LocaltonetManager
from src.bot.config import IPROXY_API_KEY, LOCALTONET_API_KEY
import logging

iproxy_manager = IProxyManager(IPROXY_API_KEY)
localtonet_manager = LocaltonetManager(LOCALTONET_API_KEY)

async def sync_proxy_connections():
    while True:
        print("Syncing db with services...")
        await iproxy_manager.sync_connections()
        await localtonet_manager.sync_connections()
        print("Db synced!")
        await asyncio.sleep(3600)  # Synchronize every hour
