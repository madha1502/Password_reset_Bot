import os
import sys
from sqlalchemy.orm import Session

# Add current folder to path to enable imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import User, OTPCode, AuditLog, MockEmail, ChatSession
from agent import hash_password

def seed_db():
    print("[Seed] Initializing database and creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Clear existing entries
        print("[Seed] Clearing old tables...")
        db.query(OTPCode).delete()
        db.query(AuditLog).delete()
        db.query(MockEmail).delete()
        db.query(ChatSession).delete()
        db.query(User).delete()
        db.commit()

        # Seed mock users
        mock_users = [
            ("Admin", "admin@example.com", "adminpass123"),
            ("Regular User", "user@example.com", "userpass456"),
            ("Test User", "test@example.com", "testpass789"),
            ("John Doe", "john.doe@company.com", "companysecure123")
        ]
        
        print("[Seed] Seeding mock users...")
        for name, email, password in mock_users:
            hashed = hash_password(password)
            new_user = User(name=name, email=email, password_hash=hashed)
            db.add(new_user)
        
        db.commit()
        print("[Seed] Successfully seeded database with default users:")
        for name, email, password in mock_users:
            print(f"  - Name: {name} | Email: {email} | Password: {password}")
            
    except Exception as e:
        print(f"[Seed] Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
