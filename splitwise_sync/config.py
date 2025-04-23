"""Configuration utilities for the application."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GMAIL_USERNAME = os.getenv("GMAIL_USERNAME", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY", "")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET", "")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY", "")

DEFAULT_FRIEND_ID = int(os.getenv("DEFAULT_FRIEND_ID", "0"))
DEFAULT_SPLIT = float(os.getenv("DEFAULT_SPLIT", "0.5"))

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

LOGS_DIR = Path(os.getenv("LOGS_DIR", ""))
if not LOGS_DIR.exists():
    logger.info(f"Creating directory for processed logs: {LOGS_DIR}")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
