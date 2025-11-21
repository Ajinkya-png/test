"""
App Initialization
==================

Initializes the Food Delivery Voice AI backend package.
This ensures all modules (agents, routers, services, etc.)
are importable and properly configured.

Executed automatically when the `app` package is imported.
"""

import logging
from .core import config

# Initialize logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Initializing Food Delivery Voice AI Application...")

# Preload environment configuration
settings = config.settings

# Confirm key components loaded
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info("✅ App package initialized successfully.")
