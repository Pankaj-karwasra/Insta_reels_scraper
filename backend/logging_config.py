import logging
import os


LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()


def configure_logging():
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
    level=level,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    )