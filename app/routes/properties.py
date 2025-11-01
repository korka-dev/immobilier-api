import os
import uuid
import json
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy.orm import Session
import cloudinary.uploader

from app.database import get_db
from app.oauth2 import get_current_user
from app.models.property import Property
from app.models.user import User
from app.schemas.property import PropertyOut, PropertyOutWithOwner, PropertyStatusUpdate
from app.schemas.user import UserPublic

router = APIRouter(prefix="/posts", tags=["Posts"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


async def save_upload_file_to_cloudinary(upload_file: UploadFile) -> str:
    """Upload file to Cloudinary and return URL"""
    if not is_allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed ({upload_file.filename})"
        )
    
    # Save temporarily
    temp_file_path = f"temp_{uuid.uuid4()}{os.path.splitext(upload_file.filename)[1]}"
    with open(temp_file_path, "wb") as f:
        f.write(await upload_file.read())
    
    # Upload to Cloudinary
    result = cloudinary.uploader.upload(temp_file_path, folder="immobilier")
    
    # Remove temp file
    os.remove(temp_file_path)
    
    return result["secure_url"]


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
    images: str = Form(...),  # Now expects JSON string of base64 images from upload.py
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property with images from upload endpoint"""
    try:
        image_list = json.loads(images)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Images must be a valid JSON array"
        )

    # Parse equipement
    try:
        equipement_list = json.loads(equipement)
    except json.JSONDecodeError:
        equipement_list = [equipement]

    # Create property
    property_obj = Property(
        id=str(uuid.uuid4()),
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
        images=image_list,
        owner_id=current_user.id,
        status=status
    )

    db.add(property_obj)
    db.commit()
    db.refresh(property_obj)

    return property_obj


@router.get("/public/all", response_model=List[PropertyOutWithOwner])
async def get_all_properties(db: Session = Depends(get_db)):
    """Get all public properties with owner info"""
    properties = db.query(Property).filter(Property.status == "en cours").all()
    
    results = []
    for prop in properties:
        owner_data = None
        if prop.owner:
            owner_data = UserPublic(
                name=prop.owner.name,
                email=prop.owner.email,
                agence=prop.owner.agence,
                contact=prop.owner.contact
            )
        
        results.append(PropertyOutWithOwner(
            id=prop.id,
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


@router.get("/my-properties", response_model=List[PropertyOut])
async def get_my_properties(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's properties"""
    properties = db.query(Property).filter(Property.owner_id == current_user.id).all()
    return properties


@router.get("/public/{property_id}", response_model=PropertyOutWithOwner)
async def get_property_details(property_id: str, db: Session = Depends(get_db)):
    """Get property details with owner info"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    owner_data = None
    if property_obj.owner:
        owner_data = UserPublic(
            name=property_obj.owner.name,
            email=property_obj.owner.email,
            agence=property_obj.owner.agence,
            contact=property_obj.owner.contact
        )
    
    return PropertyOutWithOwner(
        id=property_obj.id,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update property status"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

    property_obj.status = status_update.status
    db.commit()
    db.refresh(property_obj)
    
    return property_obj


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
    images: Optional[str] = Form(None),  # Now expects JSON string of base64 images
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update property"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

    # Update fields
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

    if images is not None:
        try:
            new_images = json.loads(images)
            property_obj.images.extend(new_images)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Images must be a valid JSON array"
            )

    db.commit()
    db.refresh(property_obj)
    
    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete property"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if property_obj.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

    db.delete(property_obj)
    db.commit()
    
    return None
