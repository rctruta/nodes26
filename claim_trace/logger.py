"""One logging setup for the package."""
import logging

from claim_trace.constants import LOG_FORMAT


def configure(level: str) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
