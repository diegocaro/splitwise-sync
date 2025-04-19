"""Configuration utilities for the application."""

import os

from dotenv import load_dotenv

load_dotenv()

GMAIL_USERNAME = os.getenv("GMAIL_USERNAME", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

SPLITWISE_CONSUMER_KEY = os.getenv("SPLITWISE_CONSUMER_KEY", "")
SPLITWISE_CONSUMER_SECRET = os.getenv("SPLITWISE_CONSUMER_SECRET", "")
SPLITWISE_API_KEY = os.getenv("SPLITWISE_API_KEY", "")

DEFAULT_FRIEND_ID = int(os.getenv("DEFAULT_FRIEND_ID", "0"))
DEFAULT_SPLIT = float(os.getenv("DEFAULT_SPLIT", "0.5"))


DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
