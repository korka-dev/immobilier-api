import os
import uuid
import json
from bson import ObjectId
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from typing import List, Optional

import cloudinary.uploader

from app import oauth2
from app.models.post import Property
from app.schemas.post import PropertyOut, PropertyOutWithOwner, PropertyStatusUpdate, UserPublic
from app.models.user import User

router = APIRouter(prefix="/posts", tags=["Posts"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

async def save_upload_file_to_cloudinary(upload_file: UploadFile) -> str:
    if not is_allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed ({upload_file.filename})"
        )
    
    # Sauvegarde temporaire
    temp_file_path = f"temp_{uuid.uuid4()}{os.path.splitext(upload_file.filename)[1]}"
    with open(temp_file_path, "wb") as f:
        f.write(await upload_file.read())
    
    # Upload sur Cloudinary
    result = cloudinary.uploader.upload(temp_file_path, folder="immobilier")
    
    # Supprimer le fichier temporaire
    os.remove(temp_file_path)
    
    return result["secure_url"]  # <- Cette URL sera stockée en DB

# ------------------------------
# Créer une nouvelle propriété
# ------------------------------
@router.post("/create", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
async def create_property(
    title: str = Form(...),
    price: float = Form(...),
    type: str = Form(...),
    localisation: str = Form(...),
    adresse_complet: str = Form(...),
    description: str = Form(...),
    surface: float = Form(...),
    chambres: int = Form(...),
    salle_de_bain: int = Form(...),
    equipement: str = Form(...),
    status: str = Form("en cours"),
    images: List[UploadFile] = File(...),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Upload images sur Cloudinary et récupération des URLs
    image_urls = [await save_upload_file_to_cloudinary(img) for img in images if img.filename]

    # Gestion du champ equipement
    try:
        equipement_list = json.loads(equipement)
    except json.JSONDecodeError:
        equipement_list = [equipement]

    # Création de la propriété
    property_obj = Property(
        title=title,
        price=price,
        type=type,
        localisation=localisation,
        adresse_complet=adresse_complet,
        description=description,
        surface=surface,
        chambres=chambres,
        salle_de_bain=salle_de_bain,
        equipement=equipement_list,
        images=image_urls,  # <-- stocke les URLs Cloudinary
        owner=current_user,
        status=status
    )

    await property_obj.insert()

    prop_dict = property_obj.dict()
    prop_dict["id"] = str(property_obj.id)
    prop_dict["owner_id"] = str(current_user.id)

    return PropertyOut(**prop_dict)

# ------------------------------
# Récupérer toutes les propriétés publiques
# ------------------------------
@router.get("/public/all", response_model=List[PropertyOutWithOwner])
async def get_all_properties():
    properties = await Property.find(Property.status == "en cours").to_list()
    
    # Collecter tous les owner IDs
    owner_ids = [str(prop.owner.ref.id) for prop in properties if prop.owner and hasattr(prop.owner, "ref")]

    # Charger tous les owners en une seule requête
    owners_dict = {}
    if owner_ids:
        owners = await User.find({"_id": {"$in": owner_ids}}).to_list()
        owners_dict = {str(owner.id): owner for owner in owners}
    
    results = []
    for prop in properties:
        owner_data = None
        if prop.owner and hasattr(prop.owner, "ref"):
            owner_id = str(prop.owner.ref.id)
            if owner_id in owners_dict:
                owner = owners_dict[owner_id]
                owner_data = UserPublic(
                    name=owner.name,
                    email=owner.email,
                    agence=owner.agence,
                    contact=owner.contact
                )
        results.append(PropertyOutWithOwner(
            id=str(prop.id),
            title=prop.title,
            price=prop.price,
            type=prop.type,
            localisation=prop.localisation,
            adresse_complet=prop.adresse_complet,
            description=prop.description,
            surface=prop.surface,
            chambres=prop.chambres,
            salle_de_bain=prop.salle_de_bain,
            equipement=prop.equipement,
            images=prop.images,
            status=prop.status,
            owner=owner_data,
            created_at=prop.created_at
        ))
    return results

# ------------------------------
# Récupérer les propriétés d'un utilisateur
# ------------------------------
@router.get("/my-properties", response_model=List[PropertyOut])
async def get_my_properties(current_user: User = Depends(oauth2.get_current_user)):
    properties = await Property.find({"owner.$id": current_user.id}).to_list()
    results = [PropertyOut(
        id=str(prop.id),
        title=prop.title,
        price=prop.price,
        type=prop.type,
        localisation=prop.localisation,
        adresse_complet=prop.adresse_complet,
        description=prop.description,
        surface=prop.surface,
        chambres=prop.chambres,
        salle_de_bain=prop.salle_de_bain,
        equipement=prop.equipement,
        images=prop.images,
        status=prop.status,
        created_at=prop.created_at
    ) for prop in properties]
    return results

# ------------------------------
# Récupérer une propriété spécifique
# ------------------------------
@router.get("/public/{property_id}", response_model=PropertyOutWithOwner)
async def get_property_details(property_id: str):
    try:
        property_obj = await Property.get(ObjectId(property_id))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid property ID format")

    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    owner_data = None
    if property_obj.owner and hasattr(property_obj.owner, "ref"):
        owner = await User.get(property_obj.owner.ref.id)
        if owner:
            owner_data = UserPublic(
                name=owner.name,
                email=owner.email,
                agence=owner.agence,
                contact=owner.contact
            )
    return PropertyOutWithOwner(
        id=str(property_obj.id),
        title=property_obj.title,
        price=property_obj.price,
        type=property_obj.type,
        localisation=property_obj.localisation,
        adresse_complet=property_obj.adresse_complet,
        description=property_obj.description,
        surface=property_obj.surface,
        chambres=property_obj.chambres,
        salle_de_bain=property_obj.salle_de_bain,
        equipement=property_obj.equipement,
        images=property_obj.images,
        status=property_obj.status,
        owner=owner_data,
        created_at=property_obj.created_at
    )

# ------------------------------
# Mettre à jour le statut d'une propriété
# ------------------------------
@router.patch("/{property_id}/status", response_model=PropertyOut)
async def update_property_status(
    property_id: str,
    status_update: PropertyStatusUpdate,
    current_user: User = Depends(oauth2.get_current_user)
):
    property_obj = await Property.get(ObjectId(property_id))
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if not (property_obj.owner and hasattr(property_obj.owner, "ref")) or property_obj.owner.ref.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

    property_obj.status = status_update.status
    await property_obj.save()
    
    return PropertyOut(**property_obj.dict())

# ------------------------------
# Mettre à jour une propriété (y compris les images)
# ------------------------------
@router.patch("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: str,
    title: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    type: Optional[str] = Form(None),
    localisation: Optional[str] = Form(None),
    adresse_complet: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    surface: Optional[float] = Form(None),
    chambres: Optional[int] = Form(None),
    salle_de_bain: Optional[int] = Form(None),
    equipement: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(oauth2.get_current_user)
):
    try:
        property_obj = await Property.get(ObjectId(property_id))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid property ID format")

    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if not (property_obj.owner and hasattr(property_obj.owner, "ref")) or property_obj.owner.ref.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

    # Mise à jour partielle
    for field, value in [("title", title), ("price", price), ("type", type),
                         ("localisation", localisation), ("adresse_complet", adresse_complet),
                         ("description", description), ("surface", surface),
                         ("chambres", chambres), ("salle_de_bain", salle_de_bain)]:
        if value is not None:
            setattr(property_obj, field, value)

    if equipement is not None:
        try:
            property_obj.equipement = json.loads(equipement)
        except json.JSONDecodeError:
            property_obj.equipement = [equipement]

    if images:
        new_image_urls = [await save_upload_file_to_cloudinary(img) for img in images if img.filename]
        property_obj.images.extend(new_image_urls)

    await property_obj.save()
    return PropertyOut(**property_obj.dict())

# ------------------------------
# Supprimer une propriété
# ------------------------------
@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(property_id: str, current_user: User = Depends(oauth2.get_current_user)):
    try:
        property_obj = await Property.get(ObjectId(property_id))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid property ID format")

    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if not (property_obj.owner and hasattr(property_obj.owner, "ref")) or property_obj.owner.ref.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

    await property_obj.delete()
    return None
