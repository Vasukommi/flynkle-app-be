from app.core.config import settings
from app.db.base import Base
from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

# ✅ Load .env
from dotenv import load_dotenv
load_dotenv()

# ✅ Import models + Base


# ✅ Configure alembic
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
