from pydantic import BaseModel, EmailStr
from datetime import datetime

class AuthStartResponse(BaseModel):
    authorization_url: str
    state: str

class AuthCallbackRequest(BaseModel):
    code: str
    state: str

class AuthCallbackResponse(BaseModel):
    user_email: EmailStr
    session_token: str
    expires_at: datetime

class TokenRefreshResponse(BaseModel):
    access_token: str
    expires_at: datetime
