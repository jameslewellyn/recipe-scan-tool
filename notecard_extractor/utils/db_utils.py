#!/usr/bin/env python3
"""
Database utility functions.
Handles database session management and common operations.
"""

from contextlib import contextmanager
from typing import Optional
from sqlalchemy.engine import Engine
from sqlmodel import Session


# Global database engine (will be set by web_gui)
_db_engine: Optional[Engine] = None


def set_db_engine(engine: Engine) -> None:
    """
    Set the global database engine.
    
    Args:
        engine: SQLAlchemy engine
    """
    global _db_engine
    _db_engine = engine


def get_db_engine() -> Optional[Engine]:
    """
    Get the global database engine.
    
    Returns:
        Database engine or None if not initialized
    """
    return _db_engine


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    
    Yields:
        SQLModel Session
        
    Raises:
        RuntimeError: If database engine is not initialized
    """
    if _db_engine is None:
        raise RuntimeError("Database engine not initialized")
    
    with Session(_db_engine) as session:
        yield session
