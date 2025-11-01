import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserRequest, UserUpdateContact
from app.oauth2 import get_current_user
from app.utils import hashed, send_account_created_email, send_user_request_email

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/create", response_model=UserOut)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    plain_password = user.password
    
    # Create new user
    user_obj = User(
        id=str(uuid.uuid4()),
        name=user.name,
        email=user.email,
        password=hashed(user.password),
        agence=user.agence,
        contact=user.contact
    )
    
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    
    try:
        await send_account_created_email(
            client_email=user.email,
            client_name=user.name,
            password=plain_password
        )
    except Exception as e:
        # Log error but don't fail the user creation
        print(f"Warning: Failed to send email to {user.email}: {e}")
    
    return user_obj


@router.get("/all", response_model=list[UserOut])
async def get_all_users(db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).all()
    return users


@router.get("/profil", response_model=UserOut)
async def get_user_infos(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/contact", response_model=UserOut)
async def update_own_contact(
    update: UserUpdateContact,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's contact"""
    current_user.contact = update.contact
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/send-request", status_code=status.HTTP_201_CREATED)
async def create_user_request(request: UserRequest):
    """Send user account request to admin"""
    try:
        await send_user_request_email(
            name=request.name,
            email=request.email,
            agence=request.agence,
            contact=request.contact
        )
        return {"message": "Votre demande a été envoyée avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email : {e}")


@router.post("/send-account-email", status_code=status.HTTP_200_OK)
async def send_account_email(client_email: str, client_name: str, password: str):
    """Send account credentials to client"""
    try:
        await send_account_created_email(
            client_email=client_email,
            client_name=client_name,
            password=password
        )
        return {"message": f"Email envoyé avec succès à {client_email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email : {e}")
