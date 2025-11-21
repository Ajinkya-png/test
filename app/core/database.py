from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis.asyncio as aioredis
from ..core.config import settings

# PostgreSQL Database (SQLAlchemy)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis for session storage (async client)
# Use redis.asyncio so state_manager can await Redis operations
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


def get_db():
    """
    Dependency that yields a SQLAlchemy session.
    Typical usage in FastAPI:
        db = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
