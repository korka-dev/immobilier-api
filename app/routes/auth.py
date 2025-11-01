from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import oauth2, utils
from app.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import PasswordChange

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    # Search user by email
    user = db.query(User).filter(User.email == user_credentials.username).first()

    if user is None or not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials"
        )

    # Create JWT token
    access_token = oauth2.create_access_token(
        data={"user_id": user.id, "user_name": user.name}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.name
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db)
):
    """
    Change user password by providing email, old password and new password
    """
    # Find user by email
    user = db.query(User).filter(User.email == password_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not utils.verify(password_data.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect old password"
        )
    
    # Hash and update new password
    user.password = utils.hashed(password_data.new_password)
    db.commit()
    
    return {
        "message": "Password changed successfully"
    }
