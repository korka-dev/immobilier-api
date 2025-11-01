from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr
    agence: Optional[str] = None
    contact: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    agence: Optional[str] = None
    contact: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserPublic(BaseModel):
    name: str
    email: EmailStr
    agence: str
    contact: str

    model_config = {
        "from_attributes": True
    }


class UserUpdateContact(BaseModel):
    contact: str


class UserRequest(BaseModel):
    name: str
    email: EmailStr
    agence: str
    contact: str


class PasswordChange(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str
