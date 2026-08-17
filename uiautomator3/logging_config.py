"""Unified logging setup for UIAutomator 3.0."""
import logging
from typing import Optional

_LOGGER_NAME = "uiautomator3"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    full_name = _LOGGER_NAME if not name else f"{_LOGGER_NAME}.{name}"
    return logging.getLogger(full_name)


def configure_logging(level: str = "INFO") -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level.upper())
