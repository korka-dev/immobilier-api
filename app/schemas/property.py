from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, validator

from app.schemas.user import UserPublic


class PropertyBase(BaseModel):
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
    status: str = "en cours"


class PropertyOut(BaseModel):
    id: str
    title: str
    price: float
    type: str
    localisation: str
    adresse_complet: str
    description: str
    surface: float
    chambres: int
    status: str
    salle_de_bain: int
    equipement: List[str]
    images: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyOutWithOwner(PropertyOut):
    owner: Optional[UserPublic] = None


class PropertyStatusUpdate(BaseModel):
    status: str
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["en cours", "vendu", "loué", "retiré"]:
            raise ValueError('Status must be one of: "en cours", "vendu", "loué", "retiré"')
        return v
