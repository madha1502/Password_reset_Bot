import os
import re
import random
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import User, OTPCode, AuditLog, ChatSession
from email_service import send_otp_email
import hashlib

# SHA-256 password hashing helper
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Generates 6-digit OTP
def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

# Audit logger helper
def log_audit(db: Session, email: str, action: str):
    log = AuditLog(email=email, action=action, timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    print(f"[Audit Log] {email} - {action} at {log.timestamp}")

# Rule-Based State Machine Fallback (used when Ollama is offline)
def process_fallback_state(db: Session, session: ChatSession, message: str) -> str:
    message_lower = message.lower().strip()

    # Restart workflow if completed and user requests a new reset
    if session.current_step == "COMPLETED" or session.current_step == "START":
        reset_keywords = ["reset", "forgot", "login", "recover", "password", "account", "can't log in", "cant login"]
        if any(kw in message_lower for kw in reset_keywords):
            session.current_step = "AWAITING_EMAIL"
            session.email = None
            session.verified = False
            db.commit()
            
            # Check if email is already in the first message
            email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", message)
            if email_match:
                email = email_match.group(0).strip()
                return handle_provided_email(db, session, email)
                
            log_audit(db, "anonymous", "RESET_REQUESTED")
            return "I can help with that. Please provide your registered email."
        else:
            return "Hello! I am the IT Helpdesk Assistant. If you forgot your password or can't log in, just let me know and we can get it reset."

    if session.current_step == "AWAITING_EMAIL":
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", message)
        if not email_match:
            return "I didn't catch a valid email address. Please enter your registered email (e.g. user@example.com)."
        
        email = email_match.group(0).strip()
        return handle_provided_email(db, session, email)

    if session.current_step == "AWAITING_OTP":
        otp_match = re.search(r"\b\d{6}\b", message)
        if not otp_match:
            return "Please enter the 6-digit verification code sent to your email address."

        otp = otp_match.group(0).strip()
        return handle_provided_otp(db, session, otp)

    if session.current_step == "AWAITING_NEW_PASSWORD":
        new_password = message.strip()
        if len(new_password) < 6:
            return "For security reasons, your new password must be at least 6 characters long. Please enter a stronger password."
        
        return handle_password_reset(db, session, new_password)

    return "I am here to help you reset your password. Please let me know how I can assist."

# Core state transition handlers called by both LLM and Fallback
def handle_provided_email(db: Session, session: ChatSession, email: str) -> str:
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    log_audit(db, email, "RESET_REQUESTED")
    
    if not user:
        # We log that user was not found for auditable attempts
        log_audit(db, email, "RESET_FAILED_USER_NOT_FOUND")
        return f"I couldn't find an account matching '{email}'. Please check the spelling and try again."

    log_audit(db, email, "USER_FOUND")
    
    # Generate OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save OTP
    otp_code = OTPCode(email=email, otp=otp, expires_at=expires_at)
    db.add(otp_code)
    db.commit()
    log_audit(db, email, "OTP_GENERATED")
    
    # Send email
    sent = send_otp_email(db, email, otp)
    if sent:
        log_audit(db, email, "OTP_SENT")
    
    # Update Session State
    session.email = email
    session.current_step = "AWAITING_OTP"
    db.commit()
    
    return f"I have verified your account and sent a 6-digit OTP code to {email}. Please enter the OTP to verify your identity."

def handle_provided_otp(db: Session, session: ChatSession, otp: str) -> str:
    email = session.email
    if not email:
        session.current_step = "AWAITING_EMAIL"
        db.commit()
        return "It looks like we missed your email. Please provide your registered email."

    # Validate OTP
    db_otp = db.query(OTPCode).filter(
        OTPCode.email == email,
        OTPCode.otp == otp,
        OTPCode.expires_at > datetime.utcnow()
    ).order_by(OTPCode.expires_at.desc()).first()

    if not db_otp:
        log_audit(db, email, "OTP_VERIFICATION_FAILED")
        return "That verification code is invalid or has expired. Please check your email and enter the correct 6-digit code."

    # Successfully verified
    db.delete(db_otp)  # consume OTP
    session.verified = True
    session.current_step = "AWAITING_NEW_PASSWORD"
    db.commit()
    log_audit(db, email, "OTP_VERIFIED")
    
    return "OTP verified successfully! Now, please enter your new password."

def handle_password_reset(db: Session, session: ChatSession, new_password: str) -> str:
    email = session.email
    if not email or not session.verified:
        session.current_step = "AWAITING_EMAIL"
        session.verified = False
        db.commit()
        return "Unauthorized action. We need to start over. Please enter your registered email."

    # Find user and reset
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return "User not found. Reset cancelled."

    user.password = hash_password(new_password)
    log_audit(db, email, "PASSWORD_RESET")
    
    session.current_step = "COMPLETED"
    db.commit()
    
    return "Your password has been successfully updated! You can now log into your account. Let me know if you need help with anything else."

# Ollama LLM integration
def process_agent_chat(db: Session, session_id: str, message: str) -> tuple:
    # 1. Fetch or create session
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(
            session_id=session_id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # 2. Check if Ollama is running and Llama 3.2 is available
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        # Check endpoint
        res = requests.get(f"{ollama_url}/api/tags", timeout=1.5)
        if res.status_code == 200:
            # Ollama is running. Let's check if we can query Llama 3.2 or fallback to another model.
            # We will use llama3.2 if available, else we can request the default/first available model.
            models = [m["name"] for m in res.json().get("models", [])]
            model_to_use = "llama3.2" if "llama3.2:latest" in models or "llama3.2" in models else (models[0] if models else "llama3.2")
            
            # Formulate prompt
            system_prompt = f"""You are a helpful IT support helpdesk agent guiding the user through a password reset workflow.
Current session state:
- Step: {session.current_step}
- User Email: {session.email or 'None'}
- Identity Verified: {session.verified}

You MUST follow these rules:
1. If Step is START and they want to reset, reply helpfully asking for their registered email.
2. If Step is AWAITING_EMAIL and they provide an email, do NOT try to verify it yourself. Extract it and respond normally.
3. If Step is AWAITING_OTP, instruct them to enter the 6-digit OTP code.
4. If Step is AWAITING_NEW_PASSWORD, ask them to provide their new password.
5. Keep answers short, secure, and professional.

Analyze the user's message: "{message}"
Respond with a JSON object ONLY containing:
{{
  "response_message": "your conversational reply to the user, guiding them to the next action based on their input",
  "extracted_email": "extracted email address from the user message, or null if not present",
  "extracted_otp": "extracted 6-digit OTP code, or null if not present",
  "extracted_password": "extracted new password (only if Step is AWAITING_NEW_PASSWORD), or null if not present"
}}
Do not write anything other than the raw JSON output.
"""
            # Request LLM
            llm_res = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": system_prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=5.0
            )
            
            if llm_res.status_code == 200:
                import json
                data = json.loads(llm_res.json().get("response", "{}"))
                
                # Process the LLM's parsed entities deterministically in the state machine
                response_msg = data.get("response_message", "")
                extracted_email = data.get("extracted_email")
                extracted_otp = data.get("extracted_otp")
                extracted_password = data.get("extracted_password")
                
                # Check states and run logic
                if session.current_step == "START" or session.current_step == "COMPLETED":
                    # Intent check
                    message_lower = message.lower().strip()
                    reset_keywords = ["reset", "forgot", "login", "recover", "password", "account", "can't log in", "cant login"]
                    if any(kw in message_lower for kw in reset_keywords) or extracted_email:
                        session.current_step = "AWAITING_EMAIL"
                        session.email = None
                        session.verified = False
                        db.commit()
                        if extracted_email:
                            response_msg = handle_provided_email(db, session, extracted_email)
                        else:
                            log_audit(db, "anonymous", "RESET_REQUESTED")
                            response_msg = "I can help with that. Please provide your registered email."
                    else:
                        response_msg = "Hello! I am the IT Helpdesk Assistant. If you forgot your password, just let me know."
                
                elif session.current_step == "AWAITING_EMAIL":
                    if extracted_email:
                        response_msg = handle_provided_email(db, session, extracted_email)
                    elif not response_msg:
                        response_msg = "I need your registered email address. Please type it in."
                        
                elif session.current_step == "AWAITING_OTP":
                    # Fallback to regex if LLM missed it
                    otp_candidate = extracted_otp or (re.search(r"\b\d{6}\b", message).group(0) if re.search(r"\b\d{6}\b", message) else None)
                    if otp_candidate:
                        response_msg = handle_provided_otp(db, session, otp_candidate)
                    elif not response_msg:
                        response_msg = "Please enter the 6-digit OTP code you received."
                        
                elif session.current_step == "AWAITING_NEW_PASSWORD":
                    password_candidate = extracted_password or message.strip()
                    if password_candidate and len(password_candidate) >= 6:
                        response_msg = handle_password_reset(db, session, password_candidate)
                    else:
                        response_msg = "Your new password must be at least 6 characters long. Please type in a new password."

                return response_msg, session
    except Exception as e:
        print(f"[Agent] Ollama connection error: {e}. Falling back to Rule Engine.")

    # Fallback to Rule Engine
    response_msg = process_fallback_state(db, session, message)
    return response_msg, session
