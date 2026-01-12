from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

from app.models.base import Base
from app.models.business import Business
from app.models.user import BusinessUser
from app.models.person import Person, Relationship
from app.models.payment import PaymentRecord, PaymentStatus
from app.models.trust_score import TrustScore
from app.models.reference import Reference
from app.models.audit_log import AuditLog

# Alembic Config object
config = context.config
fileConfig(config.config_file_name)

from dotenv import load_dotenv
load_dotenv()
import os

# Target metadata for autogenerate
target_metadata = Base.metadata

# Get DATABASE_URL from environment
raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/trust"
)

# For migrations, force psycopg2 and require SSL if Supabase
sync_url = raw_url.replace("+asyncpg", "+psycopg2")
if "supabase.co" in sync_url and "sslmode" not in sync_url:
    sync_url += "?sslmode=require"

def run_migrations_offline():
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    sync_url = os.getenv("DATABASE_URL_SYNC")
    if not sync_url:
        raise RuntimeError("DATABASE_URL_SYNC not set")

    connectable = engine_from_config(
        {"sqlalchemy.url": sync_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
