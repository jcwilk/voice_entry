#!/usr/bin/env python3

import os
import logging
from datetime import datetime

# Set up logging to file
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_entry.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also log to stdout
    ]
)

def log_debug(msg: str) -> None:
    logging.debug(msg)

def log_info(msg: str) -> None:
    logging.info(msg)

def log_warning(msg: str) -> None:
    logging.warning(msg)

def log_error(msg: str) -> None:
    logging.error(msg)

def log_exception(msg: str) -> None:
    logging.exception(msg) 