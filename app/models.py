from sqlmodel import SQLModel, Field, Relationship
import uuid
from datetime import datetime
from pydantic import EmailStr
from typing import Optional, List
from enum import Enum

def get_random_uuid():
    return str(uuid.uuid4())


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True, index=True, default_factory=get_random_uuid)
    username: str = Field(...)
    email: EmailStr = Field(..., unique=True, index=True)
    hashed_password: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    refresh_tokens: List['RefreshToken'] = Relationship(back_populates="user", cascade_delete=True)
    sessions: List['Session'] = Relationship(back_populates="user", cascade_delete=True)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    token: str = Field(primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)
    user_id: str = Field(index=True, foreign_key='users.id', ondelete='CASCADE')
    user: 'User' = Relationship(back_populates="refresh_tokens")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True, index=True, default_factory=get_random_uuid)
    user_id: str = Field(index=True, foreign_key='users.id', ondelete='CASCADE')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    message_id: str = Field(index=True, foreign_key='messages.id')
    user: 'User' = Relationship(back_populates="sessions")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(primary_key=True, index=True, default_factory=get_random_uuid)
    session_id: str = Field(index=True, foreign_key='sessions.id', ondelete='CASCADE')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    role: Role = Field(...)
    content: str = Field(...)
