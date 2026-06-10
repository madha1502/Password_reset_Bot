import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reset_bot.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def run_migrations(engine):
    inspector = inspect(engine)
    
    if not inspector.has_table("users"):
        return
        
    columns = [col["name"] for col in inspector.get_columns("users")]
    with engine.begin() as conn:
        if "password" in columns and "password_hash" not in columns:
            try:
                conn.execute(text("ALTER TABLE users RENAME COLUMN password TO password_hash"))
            except Exception as e:
                print(f"[Migration Warning] Could not rename password column: {e}. Trying ADD COLUMN.")
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
                    conn.execute(text("UPDATE users SET password_hash = password"))
                except Exception as ex:
                    print(f"[Migration Error] Could not add password_hash: {ex}")
        
        if "name" not in columns:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR"))
            except Exception as e:
                print(f"[Migration Error] Could not add name column: {e}")
                
        if "created_at" not in columns:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
            except Exception as e:
                print(f"[Migration Error] Could not add created_at column: {e}")

    if inspector.has_table("chat_sessions"):
        columns_chat = [col["name"] for col in inspector.get_columns("chat_sessions")]
        with engine.begin() as conn:
            for col_name in ["reg_name", "reg_email", "reg_password"]:
                if col_name not in columns_chat:
                    try:
                        conn.execute(text(f"ALTER TABLE chat_sessions ADD COLUMN {col_name} VARCHAR"))
                    except Exception as e:
                        print(f"[Migration Error] Could not add column {col_name} to chat_sessions: {e}")

    if inspector.has_table("otp_codes"):
        columns_otp = [col["name"] for col in inspector.get_columns("otp_codes")]
        if "is_used" not in columns_otp:
            with engine.begin() as conn:
                try:
                    conn.execute(text("ALTER TABLE otp_codes ADD COLUMN is_used BOOLEAN DEFAULT 0"))
                except Exception as e:
                    print(f"[Migration Error] Could not add column is_used to otp_codes: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
