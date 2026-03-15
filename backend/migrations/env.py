# backend/migrations/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Make sure Python can find our app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
# Import Base AND all models — Alembic needs to see them to detect changes
from app.models.base import Base
from app.models import *  # noqa: F401 — this imports all 14 models

config = context.config

# Read the DATABASE_URL from our settings
# Use localhost here (not 'postgres') because alembic runs on your machine, not in Docker
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("@postgres:", "@localhost:")
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()