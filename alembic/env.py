from dotenv import load_dotenv
import os
load_dotenv()

from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
from app.core.database import Base
from app.core.config import settings
from app.models.database import *
import app.models


# Load alembic config
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use sync driver ONLY for alembic
url = settings.DATABASE_URL  # must be psycopg2

# Import models so Alembic can detect them
import app.models  # <-- IMPORTANT

# Alembic Autogenerate target
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
