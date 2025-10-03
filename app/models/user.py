from beanie import Document
from pydantic import EmailStr
from datetime import datetime
from bson import ObjectId
from pydantic import Field

class User(Document):
    name: str
    email: EmailStr
    password: str
    agence: str
    contact: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    class Config:
        json_encoders = {ObjectId: str}

