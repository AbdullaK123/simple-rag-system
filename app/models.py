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
    username: str = Field(..., unique=True, index=True)
    email: EmailStr = Field(..., unique=True, index=True)
    hashed_password: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
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
    title: Optional[str] = Field(default=None)  # Optional session title
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    user: 'User' = Relationship(back_populates="sessions")
    messages: List['Message'] = Relationship(back_populates="session", cascade_delete=True)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(primary_key=True, index=True, default_factory=get_random_uuid)
    session_id: str = Field(index=True, foreign_key='sessions.id', ondelete='CASCADE')
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    role: Role = Field(..., index=True)
    content: str = Field(...)
    token_count: Optional[int] = Field(default=None)  # Track token usage for cost monitoring
    session: 'Session' = Relationship(back_populates='messages')
