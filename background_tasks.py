import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.iproxy_service import IProxyService
from services.iproxy_manager import IProxyManager
from repositories.iproxy_repository import IProxyRepository
from config.database import SessionLocal

scheduler = AsyncIOScheduler()

async def daily_iproxy_sync():
    session = SessionLocal()
    try:
        iproxy_manager = IProxyManager("YOUR_API_KEY_HERE")
        iproxy_repository = IProxyRepository(session)
        iproxy_service = IProxyService(iproxy_manager, iproxy_repository, session)
        await iproxy_service.sync_connections()
    finally:
        session.close()

def start_scheduler():
    scheduler.add_job(daily_iproxy_sync, CronTrigger(hour=0))  # Run daily at midnight
    scheduler.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    start_scheduler()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()