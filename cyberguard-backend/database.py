# database.py - CyberGuard
# DB file project folder ke bahar rakhi hai, taaki Live Server / koi bhi
# file watcher DB badalne par page reload na kare.
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_DIR = Path.home() / "cyberguard_data"
DB_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{(DB_DIR / 'cyberguard.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()