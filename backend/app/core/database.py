# backend/app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# create_engine builds the connection pool to PostgreSQL
# pool_pre_ping=True: checks connection is alive before using it
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,        # max 10 simultaneous DB connections
    max_overflow=20,     # allow 20 extra connections under heavy load
    echo=settings.DEBUG  # print SQL queries to console when DEBUG=True
)

# SessionLocal is a factory — call it to get a new DB session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — inject this into any route that needs DB access.
    Usage:  def my_route(db: Session = Depends(get_db)):
    
    The 'finally' block guarantees the session closes even if an
    exception is raised inside the route.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()