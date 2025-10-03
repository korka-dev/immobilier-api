from passlib.context import CryptContext
import os
from datetime import datetime
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashed(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_filename(filename: str) -> str:
    base, ext = os.path.splitext(filename)

    return f"{base}_{datetime.utcnow()}{ext}"


def authenticate_user(username: str, password: str):
    user = User.objects(username=username).first()

    if user is None:
        return None  

    if not verify(password, user.password):
        return None  

    return user 
