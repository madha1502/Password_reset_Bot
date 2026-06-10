import os
import re
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import engine, Base, get_db, run_migrations
from models import User, OTPCode, AuditLog, MockEmail, ChatSession
from schemas import (
    ResetRequest,
    VerifyOTPRequest,
    PasswordResetRequest,
    AuditLogResponse,
    ChatRequest,
    ChatResponse,
    MockEmailResponse,
    UserResponse,
    RegisterRequest
)
from agent import (
    process_agent_chat,
    generate_otp,
    hash_password,
    log_audit,
    send_otp_email,
    hash_otp
)

# Initialize FastAPI App
app = FastAPI(
    title="AI Password Reset Walkthrough Bot API",
    description="Backend services for simulated password reset flows",
    version="1.0.0"
)

# CORS Configuration
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins:
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
else:
    allowed_origins = [
        "https://password-reset-bot-five.vercel.app",
        "https://password-reset-bot-git-main-madha1502s-projects.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
Base.metadata.create_all(bind=engine)
run_migrations(engine)

# Auto-seed mock users if table is empty
@app.on_event("startup")
def startup_populate_db():
    db = next(get_db())
    try:
        run_migrations(engine)
        user_count = db.query(User).count()
        if user_count == 0:
            mock_users = [
                ("Admin", "admin@example.com", "adminpass123"),
                ("Regular User", "user@example.com", "userpass456"),
                ("Test User", "test@example.com", "testpass789"),
                ("John Doe", "john.doe@company.com", "companysecure123")
            ]
            for name, email, password in mock_users:
                hashed = hash_password(password)
                new_user = User(name=name, email=email, password_hash=hashed)
                db.add(new_user)
            db.commit()
            print("[Startup] Seeded default mock users into database.")
    except Exception as e:
        print(f"[Startup] Error seeding database: {e}")
    finally:
        db.close()

# ----------------- Core REST API Endpoints -----------------

@app.post("/forgot-password", status_code=status.HTTP_200_OK)
@app.post("/request-reset", status_code=status.HTTP_200_OK)
def forgot_password(payload: ResetRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    
    # Audit log
    log_audit(db, email, "RESET_REQUESTED")
    
    # Validate email format
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, email):
        log_audit(db, email, "INVALID_EMAIL_FORMAT")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        log_audit(db, email, "USER_NOT_FOUND")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email."
        )
    
    log_audit(db, email, "USER_FOUND")

    # Generate secure 6-digit OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Save OTP securely (hashed)
    hashed_otp = hash_otp(otp)
    otp_code = OTPCode(email=email, otp=hashed_otp, expires_at=expires_at, is_used=False)
    db.add(otp_code)
    db.commit()
    log_audit(db, email, "OTP_GENERATED")
    
    # Send via SMTP
    sent = send_otp_email(db, email, otp)
    if sent:
        log_audit(db, email, "OTP_SENT")

    return {
        "status": "success",
        "message": "OTP has been sent to your email."
    }

@app.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    otp = payload.otp.strip()

    # Query active OTP
    hashed_otp = hash_otp(otp)
    
    # We query the database to find any OTP requests for this email to give specific errors
    any_otp = db.query(OTPCode).filter(OTPCode.email == email).order_by(OTPCode.expires_at.desc()).first()
    
    if not any_otp:
        log_audit(db, email, "OTP_VERIFICATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset request found for this email address."
        )
    
    if any_otp.is_used:
        log_audit(db, email, "OTP_VERIFICATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This OTP has already been verified and cannot be reused."
        )
        
    if any_otp.expires_at < datetime.utcnow():
        log_audit(db, email, "OTP_VERIFICATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired."
        )

    if any_otp.otp != hashed_otp:
        log_audit(db, email, "OTP_VERIFICATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP."
        )

    # Successfully verified - mark as used and prevent OTP reuse
    any_otp.is_used = True
    db.commit()
    
    log_audit(db, email, "OTP_VERIFIED")

    return {
        "status": "success",
        "message": "OTP code verified successfully.",
        "email": email,
        "verified": True
    }

@app.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    otp = payload.otp.strip()
    new_password = payload.new_password.strip()

    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Note: Password reset must only occur after successful OTP verification.
    session = db.query(ChatSession).filter(ChatSession.email == email, ChatSession.verified == True).first()
    
    hashed_otp = hash_otp(otp)
    db_otp = db.query(OTPCode).filter(
        OTPCode.email == email,
        OTPCode.otp == hashed_otp,
        OTPCode.is_used == True,
        OTPCode.expires_at > datetime.utcnow()
    ).first()
    
    if not session and not db_otp:
        log_audit(db, email, "PASSWORD_RESET_UNAUTHORIZED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password reset is unauthorized. Please verify your OTP first."
        )

    # Execute reset
    user.password_hash = hash_password(new_password)
    
    # Invalidate/delete all OTP codes for this user to prevent any potential reuse
    db.query(OTPCode).filter(OTPCode.email == email).delete()
    
    # Reset any active chat sessions verified state
    if session:
        session.verified = False
        session.current_step = "COMPLETED"
        
    db.commit()
    log_audit(db, email, "PASSWORD_RESET")

    return {
        "status": "success",
        "message": "Password has been reset successfully."
    }

@app.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db)):
    # Return sorted by timestamp descending
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return logs

# ----------------- Chat Agent API Endpoint -----------------

@app.post("/register", status_code=status.HTTP_200_OK)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    name = payload.name.strip()
    email = payload.email.strip().lower()
    password = payload.password.strip()

    # Validate name cannot be empty
    if not name:
        log_audit(db, email or "unknown", "REGISTRATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty."
        )

    # Validate email format
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, email):
        log_audit(db, email, "REGISTRATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )

    # Validate email uniqueness
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        log_audit(db, email, "REGISTRATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Validate password strength
    if len(password) < 6:
        log_audit(db, email, "REGISTRATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    log_audit(db, email, "REGISTRATION_STARTED")

    try:
        new_user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        log_audit(db, email, "USER_REGISTERED")
        return {
            "status": "SUCCESS",
            "message": "Account created successfully."
        }
    except Exception as e:
        db.rollback()
        log_audit(db, email, "REGISTRATION_FAILED")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
def chat_agent(payload: ChatRequest, db: Session = Depends(get_db)):
    session_id = payload.session_id.strip()
    message = payload.message

    # Handle agent conversational logic
    response_message, session = process_agent_chat(db, session_id, message)

    status_val = None
    actions_val = None
    if session.current_step == "AWAITING_REGISTRATION_CHOICE":
        status_val = "USER_NOT_FOUND"
        actions_val = ["register", "retry_email"]

    return ChatResponse(
        message=response_message,
        session_id=session.session_id,
        current_step=session.current_step,
        email=session.email,
        verified=session.verified,
        status=status_val,
        actions=actions_val
    )

# ----------------- Debug / Utility Endpoints -----------------

@app.get("/debug/emails", response_model=List[MockEmailResponse])
def get_mock_emails(db: Session = Depends(get_db)):
    emails = db.query(MockEmail).order_by(MockEmail.sent_at.desc()).all()
    return emails

@app.get("/debug/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.post("/debug/seed", status_code=status.HTTP_200_OK)
def trigger_seed(db: Session = Depends(get_db)):
    # Clear and re-seed database
    try:
        db.query(OTPCode).delete()
        db.query(AuditLog).delete()
        db.query(MockEmail).delete()
        db.query(ChatSession).delete()
        db.query(User).delete()
        db.commit()

        mock_users = [
            ("Admin", "admin@example.com", "adminpass123"),
            ("Regular User", "user@example.com", "userpass456"),
            ("Test User", "test@example.com", "testpass789"),
            ("John Doe", "john.doe@company.com", "companysecure123")
        ]
        for name, email, password in mock_users:
            hashed = hash_password(password)
            new_user = User(name=name, email=email, password_hash=hashed)
            db.add(new_user)
        db.commit()
        
        # Log seed action
        log_audit(db, "system", "SYSTEM_SEEDED")
        return {"status": "success", "message": "Database successfully reseeded."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed error: {e}"
        )
