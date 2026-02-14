#!/usr/bin/env python3

import os
import logging
from datetime import datetime

# Set up logging to file - keep log in project root
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voice_entry.log")

# Create a specific logger for our application
logger = logging.getLogger('voice_entry')
logger.setLevel(logging.DEBUG)

# Create handlers
file_handler = logging.FileHandler(LOG_FILE)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_debug(msg: str) -> None:
    logger.debug(msg)

def log_info(msg: str) -> None:
    logger.info(msg)

def log_warning(msg: str) -> None:
    logger.warning(msg)

def log_error(msg: str) -> None:
    logger.error(msg)

def log_exception(msg: str) -> None:
    logger.exception(msg)
