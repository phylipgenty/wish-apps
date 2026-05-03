from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    karma_score: int
    streak_count: int
    total_grants: int
    is_verified: bool
    successful_receipts: int
    is_admin: bool = False
    avatar_url: Optional[str] = None
    is_email_verified: bool = False
    bio: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None

    class Config:
        from_attributes = True


class PublicUserOut(BaseModel):
    id: int
    username: str
    karma_score: int
    total_grants: int
    avatar_url: Optional[str] = None
    is_verified: bool
    joined: Optional[datetime] = None          # from user.created_at
    bio: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None


class Token(BaseModel):
    access_token: str
    token_type: str