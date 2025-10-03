from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import oauth2, utils
from app.models.user import User  # Beanie model
from app.schemas.token import Token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    # Recherche dans MongoDB avec Beanie
    user = await User.find_one(User.email == user_credentials.username)

    if user is None or not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials"
        )

    # Création du token JWT
    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "user_name": user.name}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.name
    }

