import logging
import sys
from logging import Logger

from app.core.config import settings


def _configure_logger() -> Logger:
    """
    Configures and returns the main application logger instance
    """
    logger = logging.getLogger(settings.APPLICATION_NAME)
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Check if handlers are already configured to avoid duplicates
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


app_logger: Logger = _configure_logger()


def get_logger() -> Logger:
    """
    FastAPI Dependency Function.

    Yields the pre-configured application logger instance (app_logger).
    This function is used with Depends(get_logger) in routers and services.
    """
    return app_logger
