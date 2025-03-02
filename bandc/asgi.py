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
    from django.conf import settings
    from django.core.management import call_command

    @sync_to_async
    def acall_scrape():
        try:
            call_command("scrape")
        except Exception as exc:
            logger.exception(str(exc))

    if settings.DEBUG:
        while True:
            await acall_scrape()
            await asyncio.sleep(60 * 60)  # Sleep for 60 minutes


# Track if the task is already running
_task_started = False
_startup_lock = threading.Lock()


def ensure_background_task_started():
    global _task_started

    with _startup_lock:
        if not _task_started:
            asyncio.create_task(periodic_scrape())
            logger.info("Background periodic scraper started")
            _task_started = True


async def application(*args, **kwargs):
    ensure_background_task_started()
    await django_application(*args, **kwargs)
