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

DEFAULT_TIMEZONE = "America/Santiago"

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

LOGS_DIR = Path(os.getenv("LOGS_DIR", "./logs"))
if not LOGS_DIR.exists():
    logger.info(f"Creating directory for processed logs: {LOGS_DIR}")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Directories for data and models
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"

MODELS_DIR = PROJECT_ROOT / "models"


DEFAULT_MODEL_PATH = MODELS_DIR / "decision_tree_model.pkl"
