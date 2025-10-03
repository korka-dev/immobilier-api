from fastapi import APIRouter, HTTPException, Depends, status
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdateContact
from app.oauth2 import get_current_user
from app.utils import hashed

router = APIRouter(prefix="/users", tags=["Users"])

# ---------------------------
# Créer un utilisateur
# ---------------------------
@router.post("/create", response_model=UserOut)
async def create_user(user: UserCreate):
    # Vérifier si l'email existe déjà
    existing_user = await User.find_one({"email": user.email})

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_obj = User(
        name=user.name,
        email=user.email,
        password=hashed(user.password),
        agence=user.agence,
        contact=user.contact
    )
    await user_obj.insert()
    
    return UserOut(
        id=str(user_obj.id),
        name=user_obj.name,
        email=user_obj.email,
        agence=user_obj.agence,
        contact=user_obj.contact,
        created_at=user_obj.created_at
    )

# ---------------------------
# Récupérer tous les utilisateurs
# ---------------------------
@router.get("/all", response_model=list[UserOut])
async def get_all_users():
    users = await User.find_all().to_list()
    return [
        UserOut(
            id=str(user.id),
            name=user.name,
            email=user.email,
            agence=user.agence,
            contact=user.contact,
            created_at=user.created_at
        )
        for user in users
    ]

# ---------------------------
# Récupérer le profil de l'utilisateur connecté
# ---------------------------
@router.get("/profil", response_model=UserOut)
async def get_user_infos(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=str(current_user.id),  # ✅ Conversion ObjectId -> str
        name=current_user.name,
        email=current_user.email,
        agence=current_user.agence,
        contact=current_user.contact,
        created_at=current_user.created_at
    )

# ---------------------------
# Récupérer un utilisateur par ID
# ---------------------------
@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        agence=user.agence,
        contact=user.contact,
        created_at=user.created_at
    )

# ---------------------------
# Mettre à jour le contact de l'utilisateur connecté
# ---------------------------
@router.patch("/contact", response_model=UserOut)
async def update_own_contact(update: UserUpdateContact, current_user: User = Depends(get_current_user)):
    current_user.contact = update.contact
    await current_user.save()
    
    return UserOut(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        agence=current_user.agence,
        contact=current_user.contact,
        created_at=current_user.created_at
    )

