"""
Database Configuration and Session Management
SQLModel/SQLAlchemy setup with SQLite
"""
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
import os
from pathlib import Path

# Get the base directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Database file path
DATABASE_FILE = BASE_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create engine
# connect_args={"check_same_thread": False} is needed for SQLite
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """Create all tables in the database"""
    # Import models here to ensure they are registered with SQLModel
    from .models.user import User
    from .models.audit import Audit
    from .models.monitor import Monitor
    from .models.api_key import ApiKey
    from .models.lead import Lead
    SQLModel.metadata.create_all(engine)
    print(f"[+] Database initialized at: {DATABASE_FILE}")


def get_session() -> Generator[Session, None, None]:
    """
    Dependency to get DB session
    Usage in FastAPI routes:
        session: Session = Depends(get_session)
    """
    with Session(engine) as session:
        yield session
