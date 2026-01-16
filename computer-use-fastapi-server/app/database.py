from typing import Generator
from app.settings import settings
from sqlalchemy import Engine, event, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.settings import logger


DeclarativeBase = declarative_base()

engine: Engine= create_engine(
    url=settings.database_url,
    connect_args={
        "check_same_thread": False,
        "timeout": 100,
    },
    future=True,
)

DeclarativeBase.metadata.create_all(engine)


# Session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_session() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(message=f"Database session rollback due to error: {e}")
        raise e
    finally:
        db.close()


# SQLite PRAGMA settings
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
