"""Farmer-related schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class FarmerCreate(BaseModel):
    """Create a new farmer"""

    name: str = Field(..., min_length=1, max_length=255)
    language: str = Field(default="marathi", pattern="^(marathi|hindi|english)$")
    state: str = Field(..., min_length=1, max_length=50)
    district: Optional[str] = None
    village: Optional[str] = None
    land_size_hectares: float = Field(default=0.0, ge=0.0)
    budget_rupees: int = Field(default=0, ge=0)
    experience_level: str = Field(default="beginner", pattern="^(beginner|intermediate|expert)$")
    goals: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FarmerUpdate(BaseModel):
    """Update farmer information"""

    name: Optional[str] = None
    language: Optional[str] = None
    land_size_hectares: Optional[float] = None
    budget_rupees: Optional[int] = None
    experience_level: Optional[str] = None
    goals: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FarmerResponse(BaseModel):
    """Farmer response"""

    id: int
    farmer_id: str
    name: str
    language: str
    state: str
    district: Optional[str]
    village: Optional[str]
    land_size_hectares: float
    budget_rupees: int
    interested_enterprises: List[str]
    experience_level: str
    goals: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
