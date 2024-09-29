from apscheduler.schedulers.background import BackgroundScheduler
from price_monitor import check_pool_conditions
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    """Starts the background scheduler to periodically check pool conditions."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(check_pool_conditions()), 'interval', minutes=1, id='check_pools')
    scheduler.start()
    logger.info("Scheduler started and pool checks are running every 1 minute.")
