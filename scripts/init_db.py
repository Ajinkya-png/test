"""
Simple DB initialization helper for local dev.
Usage: python scripts/init_db.py
"""
from app.core.database import engine, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Creating database tables (SQLAlchemy Base.metadata.create_all)")
    Base.metadata.create_all(bind=engine)
    logger.info("Done.")

if __name__ == "__main__":
    main()
