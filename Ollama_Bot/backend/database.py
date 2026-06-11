import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ollama_bot.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and run migrations."""
    from backend.models import User, OTPCode, AuditLog, RiskLog, ChatHistory  # noqa
    Base.metadata.create_all(bind=engine)
    run_migrations()
    print("[DB] Database initialized.")


def run_migrations():
    """Safely add missing columns to existing tables."""
    inspector = inspect(engine)
    if inspector.has_table("otp_codes"):
        cols = [c["name"] for c in inspector.get_columns("otp_codes")]
        if "is_used" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE otp_codes ADD COLUMN is_used BOOLEAN DEFAULT 0"))
    if inspector.has_table("audit_logs"):
        cols = [c["name"] for c in inspector.get_columns("audit_logs")]
        if "ip_address" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN ip_address VARCHAR"))
