from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

from app.config.settings import settings

DATABASE_URL = os.getenv("DATABASE_URL") or settings.database_url

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def ensure_postgis(conn):
    # Run once per startup to ensure PostGIS extension exists (idempotent)
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    conn.commit()
