# Configures the SQLAlchemy connection, sessions, and table creation.
from importlib import import_module

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.settings import Settings

settings = Settings()
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    )

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def init_db():
    # Load model modules so their tables are registered in Base.metadata.
    import_module("app.storage.models")

    Base.metadata.create_all(bind = engine)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
