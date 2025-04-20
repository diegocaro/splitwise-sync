"""FastAPI endpoint for Splitwise transaction sync."""

import logging

from fastapi import FastAPI

from splitwise_sync.api.routes import api_router
from splitwise_sync.utils import config as Config

logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Splitwise Sync API",
    description="API for processing emails and creating Splitwise expenses",
    version="0.1.0",
)
app.include_router(api_router)
