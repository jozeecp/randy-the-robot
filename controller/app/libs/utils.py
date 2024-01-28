import logging
import random
import string
from pprint import pformat
from time import ctime, time
from typing import Any
from uuid import uuid4


def human_readable_time() -> str:
    return ctime(time())


def get_human_readable_ts() -> str:
    """
    Returns the current time in a human-readable format.
    Example output: 'Mon Sep 30 07:06:05 2013'
    """
    return ctime(time())


def get_unix_ts() -> float:
    """
    Returns the current time as a Unix timestamp.
    Example output: 1380471766.5738373
    """
    return time()


def create_short_uuid(length: int = 12) -> str:
    """
    Returns a hashed uuid
    """
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


def create_uuid() -> str:
    """
    Returns a uuid, use this method in case we want to change the uuid generation later
    """
    return str(uuid4())


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    def __init__(
        self, fmt: Any, datefmt: Any = "", style: Any = "%", validate: bool = True
    ):
        super().__init__(fmt, datefmt, style, validate)

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # type: ignore

    FORMATS = {
        logging.DEBUG: grey + format + reset,  # type: ignore
        logging.INFO: green + format + reset,  # type: ignore
        logging.WARNING: yellow + format + reset,  # type: ignore
        logging.ERROR: red + format + reset,  # type: ignore
        logging.CRITICAL: bold_red + format + reset,  # type: ignore
        # logging.DEBUG: format,  # type: ignore
        # logging.INFO: format,  # type: ignore
        # logging.WARNING: format,  # type: ignore
        # logging.ERROR: format,  # type: ignore
        # logging.CRITICAL: format,  # type: ignore
    }

    def format(self, record):  # type: ignore
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = CustomFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def custom_pformat(input: Any) -> Any:
    """
    Pretty print a python object. Recommend to import as pf.
    """
    from pydantic import BaseModel  # lazy import to avoid circular import

    if isinstance(input, BaseModel):
        input = input.model_dump()
    return pformat(input, indent=4, width=2)
