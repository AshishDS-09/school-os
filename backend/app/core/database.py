# # backend/app/core/database.py

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from typing import Generator
# from app.core.config import settings

# # create_engine builds the connection pool to PostgreSQL
# # pool_pre_ping=True: checks connection is alive before using it
# engine = create_engine(
#     settings.DATABASE_URL,
#     pool_pre_ping=True,
#     pool_size=10,        # max 10 simultaneous DB connections
#     max_overflow=20,     # allow 20 extra connections under heavy load
#     echo=settings.DEBUG  # print SQL queries to console when DEBUG=True
# )

# # SessionLocal is a factory — call it to get a new DB session
# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine
# )

# def get_db() -> Generator[Session, None, None]:
#     """
#     FastAPI dependency — inject this into any route that needs DB access.
#     Usage:  def my_route(db: Session = Depends(get_db)):
    
#     The 'finally' block guarantees the session closes even if an
#     exception is raised inside the route.
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# backend/app/core/database.py  — full replacement

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Standard FastAPI dependency for DB access.
    Automatically sets app.school_id on the PostgreSQL session
    so Row Level Security policies can read it.
    """
    db = SessionLocal()
    try:
        # Set the school_id for RLS — read from TenantContext
        # This runs before every request handler
        try:
            from app.core.tenant import TenantContext
            if TenantContext.is_set():
                school_id = TenantContext.get()
                db.execute(
                    text("SET LOCAL app.school_id = :sid"),
                    {"sid": str(school_id)}
                )
        except Exception:
            pass  # TenantContext not set yet (e.g. during login)

        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager version for use in agents and background tasks.
    
    Usage:
        with get_db_context() as db:
            results = db.query(Student).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()