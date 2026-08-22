"""Farmer profile model"""

from sqlalchemy import Column, Integer, String, Float, JSON, Text
from app.models.base import BaseModel


class Farmer(BaseModel):
    """Farmer profile and context"""

    __tablename__ = "farmers"

    farmer_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    language = Column(String(20), default="marathi", nullable=False)
    state = Column(String(50), nullable=False)
    district = Column(String(50), nullable=True)
    village = Column(String(255), nullable=True)

    # Resources
    land_size_hectares = Column(Float, default=0.0, nullable=False)
    budget_rupees = Column(Integer, default=0, nullable=False)

    # Interests and Background
    interested_enterprises = Column(JSON, default=[], nullable=False)
    experience_level = Column(String(20), default="beginner", nullable=False)  # beginner, intermediate, expert
    goals = Column(Text, nullable=True)

    # Contact
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # Additional context
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Farmer(id={self.id}, farmer_id={self.farmer_id}, name={self.name})>"
