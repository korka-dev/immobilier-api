from beanie import Document, Link
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import Field

from app.models.user import User 

class Property(Document):
    title: str
    price: float
    type: str
    localisation: str
    adresse_complet: str
    description: str
    surface: float
    chambres: int
    salle_de_bain: int
    equipement: List[str]
    images: List[str]
    owner: Optional[Link[User]] = None  # ← Changé ici : ajout de Optional et = None
    status: str = Field(default="en cours")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "properties"

    class Config:
        json_encoders = {ObjectId: str}