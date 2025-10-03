from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, validator

class UserPublic(BaseModel):
    name: str
    email: EmailStr
    agence: str
    contact: str

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
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PropertyOutWithOwner(PropertyOut):
    owner: Optional[UserPublic]


class PropertyStatusUpdate(BaseModel):
    status: str
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["en cours", "vendu", "loué", "retiré"]:
            raise ValueError('Status must be "en cours" or "vendu"')
        return v
    
    