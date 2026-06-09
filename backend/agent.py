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

    if session.current_step == "AWAITING_REGISTRATION_CHOICE":
        if "successfully registered" in message_lower:
            session.current_step = "COMPLETED"
            db.commit()
            return "Congratulations! Your account has been registered successfully. Let me know if you need help with anything else."
        elif "1" in message_lower or "register" in message_lower:
            session.current_step = "AWAITING_REGISTRATION_NAME"
            session.reg_name = None
            session.reg_email = None
            session.reg_password = None
            db.commit()
            log_audit(db, session.email or "anonymous", "REGISTRATION_STARTED")
            return "Registration started. Please enter your Full Name."
        elif "2" in message_lower or "another" in message_lower or "retry" in message_lower or "email" in message_lower:
            session.current_step = "AWAITING_EMAIL"
            session.email = None
            db.commit()
            return "Please enter your registered email address."
        else:
            return "No account exists with this email.\n\nWould you like to:\n1. Register New User\n2. Use Another Email"

    if session.current_step == "AWAITING_REGISTRATION_NAME":
        name = message.strip()
        if not name:
            return "Name cannot be empty. Please enter your Full Name."
        session.reg_name = name
        session.current_step = "AWAITING_REGISTRATION_EMAIL"
        db.commit()
        return f"Got it, {name}. Now, please enter your Email Address."

    if session.current_step == "AWAITING_REGISTRATION_EMAIL":
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", message)
        if not email_match:
            return "Please provide a valid Email Address (e.g., name@domain.com)."
        
        email = email_match.group(0).strip().lower()
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            log_audit(db, email, "REGISTRATION_FAILED")
            return "An account with this email already exists. Please enter a different Email Address."
        
        session.reg_email = email
        session.current_step = "AWAITING_REGISTRATION_PASSWORD"
        db.commit()
        return "Excellent. Finally, please choose a password for your new account (minimum 6 characters)."

    if session.current_step == "AWAITING_REGISTRATION_PASSWORD":
        password = message.strip()
        if len(password) < 6:
            return "Password must be at least 6 characters long. Please enter a stronger password."
        
        try:
            existing_user = db.query(User).filter(User.email == session.reg_email).first()
            if existing_user:
                log_audit(db, session.reg_email, "REGISTRATION_FAILED")
                session.current_step = "AWAITING_REGISTRATION_CHOICE"
                db.commit()
                return "An account with this email already exists. Registration failed. Would you like to:\n1. Register New User\n2. Use Another Email"

            new_user = User(
                name=session.reg_name,
                email=session.reg_email,
                password_hash=hash_password(password),
                created_at=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            log_audit(db, session.reg_email, "USER_REGISTERED")
            
            session.email = session.reg_email
            session.reg_name = None
            session.reg_email = None
            session.reg_password = None
            session.current_step = "COMPLETED"
            db.commit()
            return f"Account created successfully for {new_user.email}! Your registration is complete. Let me know if there's anything else I can assist with."
        except Exception as e:
            log_audit(db, session.reg_email or "unknown", "REGISTRATION_FAILED")
            return f"An error occurred during registration: {str(e)}. Please try again."

    return "I am here to help you reset your password. Please let me know how I can assist."

# Core state transition handlers called by both LLM and Fallback
def handle_provided_email(db: Session, session: ChatSession, email: str) -> str:
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    log_audit(db, email, "RESET_REQUESTED")
    
    if not user:
        # We log that user was not found for auditable attempts
        log_audit(db, email, "USER_NOT_FOUND")
        session.current_step = "AWAITING_REGISTRATION_CHOICE"
        session.email = email
        db.commit()
        return "No account exists with this email.\n\nWould you like to:\n1. Register New User\n2. Use Another Email"

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

    user.password_hash = hash_password(new_password)
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
            system_prompt = f"""You are a helpful IT support helpdesk agent guiding the user through a password reset or registration workflow.
Current session state:
- Step: {session.current_step}
- User Email: {session.email or 'None'}
- Identity Verified: {session.verified}
- Collected Name: {session.reg_name or 'None'}
- Collected Email: {session.reg_email or 'None'}

You MUST follow these rules:
1. If Step is START and they want to reset, reply helpfully asking for their registered email.
2. If Step is AWAITING_EMAIL and they provide an email, do NOT try to verify it yourself. Extract it and respond normally.
3. If Step is AWAITING_OTP, instruct them to enter the 6-digit OTP code.
4. If Step is AWAITING_NEW_PASSWORD, ask them to provide their new password.
5. If Step is AWAITING_REGISTRATION_CHOICE, ask if they want to (1) Register New User or (2) Use Another Email.
6. If Step is AWAITING_REGISTRATION_NAME, ask for their full name.
7. If Step is AWAITING_REGISTRATION_EMAIL, ask for their email address.
8. If Step is AWAITING_REGISTRATION_PASSWORD, ask for their new password.
9. Keep answers short, secure, and professional.

Analyze the user's message: "{message}"
Respond with a JSON object ONLY containing:
{{
  "response_message": "your conversational reply to the user guiding them to the next action based on their input",
  "extracted_email": "extracted email address from the user message, or null if not present",
  "extracted_otp": "extracted 6-digit OTP code, or null if not present",
  "extracted_password": "extracted password (only if Step is AWAITING_NEW_PASSWORD or AWAITING_REGISTRATION_PASSWORD), or null if not present",
  "extracted_name": "extracted full name (only if Step is AWAITING_REGISTRATION_NAME), or null if not present",
  "extracted_choice": "extracted registration choice ('register' or 'retry_email'), or null if not present"
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
                extracted_name = data.get("extracted_name")
                extracted_choice = data.get("extracted_choice")
                
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

                elif session.current_step == "AWAITING_REGISTRATION_CHOICE":
                    message_lower = message.lower().strip()
                    if "successfully registered" in message_lower:
                        session.current_step = "COMPLETED"
                        db.commit()
                        response_msg = "Congratulations! Your account has been registered successfully. Let me know if you need help with anything else."
                    else:
                        choice = extracted_choice or ("register" if "1" in message_lower or "register" in message_lower else ("retry_email" if "2" in message_lower or "another" in message_lower or "retry" in message_lower or "email" in message_lower else None))
                        if choice == "register":
                            session.current_step = "AWAITING_REGISTRATION_NAME"
                            session.reg_name = None
                            session.reg_email = None
                            session.reg_password = None
                            db.commit()
                            log_audit(db, session.email or "anonymous", "REGISTRATION_STARTED")
                            response_msg = "Registration started. Please enter your Full Name."
                        elif choice == "retry_email":
                            session.current_step = "AWAITING_EMAIL"
                            session.email = None
                            db.commit()
                            response_msg = "Please enter your registered email address."
                        else:
                            response_msg = "No account exists with this email.\n\nWould you like to:\n1. Register New User\n2. Use Another Email"

                elif session.current_step == "AWAITING_REGISTRATION_NAME":
                    name = extracted_name or message.strip()
                    if name:
                        session.reg_name = name
                        session.current_step = "AWAITING_REGISTRATION_EMAIL"
                        db.commit()
                        response_msg = f"Got it, {name}. Now, please enter your Email Address."
                    else:
                        response_msg = "Name cannot be empty. Please enter your Full Name."

                elif session.current_step == "AWAITING_REGISTRATION_EMAIL":
                    email_cand = extracted_email or (re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", message).group(0) if re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", message) else None)
                    if email_cand:
                        email_cand = email_cand.strip().lower()
                        existing_user = db.query(User).filter(User.email == email_cand).first()
                        if existing_user:
                            log_audit(db, email_cand, "REGISTRATION_FAILED")
                            response_msg = "An account with this email already exists. Please enter a different Email Address."
                        else:
                            session.reg_email = email_cand
                            session.current_step = "AWAITING_REGISTRATION_PASSWORD"
                            db.commit()
                            response_msg = "Excellent. Finally, please choose a password for your new account (minimum 6 characters)."
                    else:
                        response_msg = "Please provide a valid Email Address (e.g., name@domain.com)."

                elif session.current_step == "AWAITING_REGISTRATION_PASSWORD":
                    password_cand = extracted_password or message.strip()
                    if password_cand and len(password_cand) >= 6:
                        try:
                            existing_user = db.query(User).filter(User.email == session.reg_email).first()
                            if existing_user:
                                log_audit(db, session.reg_email, "REGISTRATION_FAILED")
                                session.current_step = "AWAITING_REGISTRATION_CHOICE"
                                db.commit()
                                response_msg = "An account with this email already exists. Registration failed. Would you like to:\n1. Register New User\n2. Use Another Email"
                            else:
                                new_user = User(
                                    name=session.reg_name,
                                    email=session.reg_email,
                                    password_hash=hash_password(password_cand),
                                    created_at=datetime.utcnow()
                                )
                                db.add(new_user)
                                db.commit()
                                log_audit(db, session.reg_email, "USER_REGISTERED")
                                
                                session.email = session.reg_email
                                session.reg_name = None
                                session.reg_email = None
                                session.reg_password = None
                                session.current_step = "COMPLETED"
                                db.commit()
                                response_msg = f"Account created successfully for {new_user.email}! Your registration is complete. Let me know if there's anything else I can assist with."
                        except Exception as e:
                            log_audit(db, session.reg_email or "unknown", "REGISTRATION_FAILED")
                            response_msg = f"An error occurred during registration: {str(e)}. Please try again."
                    else:
                        response_msg = "Password must be at least 6 characters long. Please enter a stronger password."

                return response_msg, session
    except Exception as e:
        print(f"[Agent] Ollama connection error: {e}. Falling back to Rule Engine.")

    # Fallback to Rule Engine
    response_msg = process_fallback_state(db, session, message)
    return response_msg, session
