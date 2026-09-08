from __future__ import annotations

import contextlib
import logging
from typing import Generator

from django.core.cache import cache

logger = logging.getLogger(__name__)

DEFAULT_LOCK_TIMEOUT = 3600


def acquire_lock(lock_name: str, timeout: int = DEFAULT_LOCK_TIMEOUT) -> bool:
    key = f"task_lock:{lock_name}"
    acquired = cache.add(key, "locked", timeout)
    if acquired:
        logger.info("lock_acquired lock_name=%s timeout=%s", lock_name, timeout)
    else:
        logger.warning("lock_conflict lock_name=%s", lock_name)
    return acquired


def release_lock(lock_name: str) -> None:
    key = f"task_lock:{lock_name}"
    cache.delete(key)
    logger.info("lock_released lock_name=%s", lock_name)


@contextlib.contextmanager
def task_lock(lock_name: str, timeout: int = DEFAULT_LOCK_TIMEOUT) -> Generator[bool, None, None]:
    acquired = acquire_lock(lock_name, timeout)
    yield acquired
