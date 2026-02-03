"""
Database Configuration and Session Management
SQLModel/SQLAlchemy setup with SQLite
"""
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
import os
from pathlib import Path
from .config import get_settings

# Get settings
settings = get_settings()

# Handle Database URL
# The .env might have "postgresql+asyncpg://..." for async context.
# For synchronous engine, we need "postgresql://" or "postgresql+psycopg2://"
DATABASE_URL = settings.database_url

if DATABASE_URL.startswith("postgresql+asyncpg"):
    # Convert to sync driver for standard requests
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

# Create engine
# connect_args is empty for Postgres, strictly only for SQLite if needed
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)


def create_db_and_tables():
    """Create all tables in the database"""
    # Import models here to ensure they are registered with SQLModel
    from .models.user import User
    from .models.audit import Audit
    from .models.monitor import Monitor
    from .models.api_key import ApiKey
    from .models.lead import Lead
    from .models.task import ScanTask
    SQLModel.metadata.create_all(engine)
    print(f"[+] Database initialized with URL: {DATABASE_URL}")


def get_session() -> Generator[Session, None, None]:
    """
    Dependency to get DB session
    Usage in FastAPI routes:
        session: Session = Depends(get_session)
    """
    with Session(engine) as session:
        yield session
