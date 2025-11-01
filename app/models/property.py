from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    localisation = Column(String, nullable=False)
    adresse_complet = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    surface = Column(Float, nullable=False)
    chambres = Column(Integer, nullable=False)
    salle_de_bain = Column(Integer, nullable=False)
    equipement = Column(ARRAY(String), nullable=False)
    images = Column(ARRAY(String), nullable=False)
    status = Column(String, default="en cours", nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    owner = relationship("User", back_populates="properties")
