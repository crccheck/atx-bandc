"""
ASGI config for bandc project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import asyncio
import logging
import os
import threading

from asgiref.sync import sync_to_async
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bandc.settings")

django_application = get_asgi_application()
logger = logging.getLogger(__name__)


async def periodic_scrape():
    from django.core.management import call_command

    @sync_to_async
    def acall_scrape():
        call_command("scrape_one")

    while True:
        try:
            await acall_scrape()
        except Exception as exc:
            logger.exception(str(exc))
        finally:
            await asyncio.sleep(15 * 60)  # Sleep for 15 minutes


# Track if the task is already running
_task_started = False
_startup_lock = threading.Lock()


def ensure_background_task_started():
    global _task_started

    with _startup_lock:
        if not _task_started:
            asyncio.create_task(periodic_scrape())  # noqa: RUF006
            logger.info("Background periodic scraper started")
            _task_started = True


async def application(*args, **kwargs):
    ensure_background_task_started()
    await django_application(*args, **kwargs)
