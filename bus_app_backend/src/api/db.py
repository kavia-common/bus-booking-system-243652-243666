"""
Database setup for the Bus Booking MVP.

Uses SQLAlchemy with a SQLite database file provided by SQLITE_DB env var.
If SQLITE_DB is not set, uses the default database container path.

This module is imported by the FastAPI app and routers.
"""
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def _sqlite_url() -> str:
    """
    Build SQLAlchemy SQLite URL from environment.

    Environment:
      - SQLITE_DB: full filesystem path to sqlite database file.
    """
    db_path = os.getenv("SQLITE_DB")
    if not db_path:
        # Default to the database container's conventional location in this repo.
        db_path = "/home/kavia/workspace/code-generation/bus-booking-system-243652-243667/bus_app_database/myapp.db"
    # Four slashes for absolute paths.
    return f"sqlite:///{db_path}"


engine = create_engine(
    _sqlite_url(),
    connect_args={"check_same_thread": False},  # needed for SQLite + threads
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
