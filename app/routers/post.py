import os
import uuid
from bson import ObjectId
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from typing import List, Optional
import json

from app import oauth2
from app.models.post import Property
from app.schemas.post import PropertyOut, PropertyOutWithOwner, PropertyStatusUpdate, UserPublic
from app.models.user import User

router = APIRouter(prefix="/posts", tags=["Posts"])

UPLOAD_DIR = "uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

async def save_upload_file(upload_file: UploadFile) -> str:
    if not is_allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed ({upload_file.filename})"
        )
    # Générer un nom unique pour éviter les collisions
    ext = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Écriture du fichier sur le disque
    with open(file_path, "wb") as f:
        f.write(await upload_file.read())
    
    return file_path  # retourne le chemin pour la DB

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
    # Upload images et récupération des chemins
    image_paths = [await save_upload_file(img) for img in images if img.filename]

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
        images=image_paths,
        owner=current_user,
        status=status
    )

    await property_obj.insert()

    # Conversion ObjectId -> str pour le frontend
    prop_dict = property_obj.dict()
    prop_dict["id"] = str(property_obj.id)
    prop_dict["owner_id"] = str(current_user.id)

    return PropertyOut(**prop_dict)


# ------------------------------
# Récupérer toutes les propriétés en cours (publique)
# ------------------------------
@router.get("/public/all", response_model=List[PropertyOutWithOwner])
async def get_all_properties():
    properties = await Property.find(
        Property.status == "en cours"
    ).to_list()
    
    # Collecter tous les owner IDs
    owner_ids = []
    for prop in properties:
        if prop.owner and hasattr(prop.owner, 'ref'):
            owner_ids.append(prop.owner.ref.id)
    
    # Charger tous les owners en une seule requête
    owners_dict = {}
    if owner_ids:
        owners = await User.find({"_id": {"$in": owner_ids}}).to_list()
        owners_dict = {str(owner.id): owner for owner in owners}
    
    results = []
    for prop in properties:
        owner_data = None
        
        if prop.owner and hasattr(prop.owner, 'ref'):
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
# Récupérer toutes les propriétés d'un utilisateur connecté (auth requise)
# ------------------------------
@router.get("/my-properties", response_model=List[PropertyOut])
async def get_my_properties(current_user: User = Depends(oauth2.get_current_user)):
    # Requête MongoDB directe sur le champ owner
    properties = await Property.find(
        {"owner.$id": current_user.id}
    ).to_list()
    
    results = []
    for prop in properties:
        results.append(PropertyOut(
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
        ))
    
    return results


# ------------------------------
# Récupérer les détails d'une propriété spécifique (publique)
# ------------------------------
@router.get("/public/{property_id}", response_model=PropertyOutWithOwner)
async def get_property_details(property_id: str):
    # Récupérer la propriété
    try:
        property_obj = await Property.get(ObjectId(property_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID format"
        )
    
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Charger les informations du propriétaire
    owner_data = None
    if property_obj.owner and hasattr(property_obj.owner, 'ref'):
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

@router.patch("/{property_id}/status", response_model=PropertyOut)
async def update_property_status(
    property_id: str,
    status_update: PropertyStatusUpdate,
    current_user: User = Depends(oauth2.get_current_user)
):
    # Récupérer la propriété
    property_obj = await Property.get(ObjectId(property_id))
    
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Vérifier que l'utilisateur est le propriétaire
    if property_obj.owner and hasattr(property_obj.owner, 'ref'):
        owner_id = property_obj.owner.ref.id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property has no owner"
        )
    
    if owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this property"
        )
    
    # Mettre à jour le statut
    property_obj.status = status_update.status
    await property_obj.save()
    
    return PropertyOut(
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
        created_at=property_obj.created_at
    )

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
    equipement: Optional[str] = Form(None),  # JSON string
    images: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(oauth2.get_current_user)
):
    # Vérifier la propriété
    try:
        property_obj = await Property.get(ObjectId(property_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID format"
        )

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Vérifier le propriétaire
    if not (property_obj.owner and hasattr(property_obj.owner, 'ref')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property has no owner"
        )
    if property_obj.owner.ref.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this property"
        )

    # Mise à jour partielle (seulement les champs envoyés)
    if title is not None:
        property_obj.title = title
    if price is not None:
        property_obj.price = price
    if type is not None:
        property_obj.type = type
    if localisation is not None:
        property_obj.localisation = localisation
    if adresse_complet is not None:
        property_obj.adresse_complet = adresse_complet
    if description is not None:
        property_obj.description = description
    if surface is not None:
        property_obj.surface = surface
    if chambres is not None:
        property_obj.chambres = chambres
    if salle_de_bain is not None:
        property_obj.salle_de_bain = salle_de_bain
    if equipement is not None:
        try:
            property_obj.equipement = json.loads(equipement)
        except json.JSONDecodeError:
            property_obj.equipement = [equipement]

    # Images → on ajoute seulement si des nouvelles sont envoyées
    if images:
        new_image_paths = [await save_upload_file(img) for img in images if img.filename]
        property_obj.images.extend(new_image_paths)  # ajoute sans supprimer les anciennes
        # Si tu veux remplacer complètement : property_obj.images = new_image_paths

    # Sauvegarde
    await property_obj.save()

    return PropertyOut(
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
        created_at=property_obj.created_at
    )

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    current_user: User = Depends(oauth2.get_current_user)
):
    # Vérifier la propriété
    try:
        property_obj = await Property.get(ObjectId(property_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID format"
        )

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Vérifier le propriétaire
    if not (property_obj.owner and hasattr(property_obj.owner, "ref")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property has no owner"
        )
    if property_obj.owner.ref.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this property"
        )

    # Supprimer la propriété
    await property_obj.delete()

    return None

