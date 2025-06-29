from __future__ import annotations

from logging import config, getLogger
from typing import TYPE_CHECKING

try:
    from .log_config import LOG_CONFIG
except ImportError:
    # Fallback for when the module is run directly
    from log_config import LOG_CONFIG

if TYPE_CHECKING:
    from logging import Logger


config.dictConfig(LOG_CONFIG)


def get_logger(name: str) -> Logger:
    return getLogger(name)


def get_root_logger() -> Logger:
    return getLogger()


if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("This is an info message.")
    logger.error("This is an error message.")
    root_logger = get_root_logger()
    root_logger.warning("This is a warning message from the root logger.")
