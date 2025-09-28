from sqlmodel import SQLModel
from datetime import datetime, timedelta
from typing import Dict, Any
from app.models import User
from app.dependencies.config import get_settings
from pydantic import EmailStr, model_validator

settings = get_settings()

class JWTClaims(SQLModel):
    sub: str
    exp: datetime
    iat: datetime

    def to_jwt_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload['exp'] = int(payload['exp'].timestamp())
        payload['iat'] = int(payload['iat'].timestamp())
        return payload

    @property
    def is_expired(self) -> bool:
        return self.exp < datetime.utcnow()

    @property
    def time_to_expire(self) -> timedelta:
        return self.exp - datetime.utcnow()

    @classmethod
    def new(cls, sub: str):
        return cls(
            sub=sub,
            exp=datetime.utcnow() + timedelta(hours=settings.auth.jwt_expiration_hours),
            iat=datetime.utcnow()
        )


class UserResponse(SQLModel):
    id: str
    username: str
    email: str

    @classmethod
    def from_user(cls, user: User):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email
        )

class UserCredentials(SQLModel):
    email: str
    password: str

class RefreshRequest(SQLModel):
    token: str

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

    @model_validator(mode='after')
    def validate_password(self):
        if len(self.password) < settings.auth.password_min_length:
            raise ValueError(f"Password must be at least {settings.auth.password_min_length} characters long")
        if self.username.strip() == "":
            raise ValueError("Username cannot be empty")
        return self

class Token(SQLModel):
    access: str
    refresh: str