import asyncio
import logging

from django.apps import AppConfig
from django.core.management import call_command

logger = logging.getLogger(__name__)


async def periodic_scrape():
    while True:
        logger.info("hello")
        # call_command("scrape")
        await asyncio.sleep(60)
        # await asyncio.sleep(60 * 60 * 24)


class AgendaConfig(AppConfig):
    name = "bandc.apps.agenda"

    def ready(self):
        asyncio.create_task(periodic_scrape())
