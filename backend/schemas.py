from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ResetRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class PasswordResetRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class AuditLogResponse(BaseModel):
    id: int
    email: str
    action: str
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    message: str
    session_id: str
    current_step: str
    email: Optional[str] = None
    verified: bool = False

class MockEmailResponse(BaseModel):
    id: int
    to_email: str
    subject: str
    body: str
    sent_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    # Password hash is returned in debug view to let developers inspect changes in real time.
    password: str

    class Config:
        orm_mode = True
        from_attributes = True
