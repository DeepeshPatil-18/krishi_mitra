"""Market-related schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MarketResponse(BaseModel):
    """Market opportunity response"""

    id: int
    product: str
    enterprise: str
    location: str
    buyer_name: Optional[str]
    buyer_type: str
    price_per_unit: Optional[float]
    currency: str
    unit_type: Optional[str]
    price_last_updated: Optional[str]
    contact_person: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    website: Optional[str]
    can_arrange_logistics: bool
    min_purchase_quantity: Optional[float]
    is_verified: bool
    is_prototype_data: bool
    created_at: datetime

    class Config:
        from_attributes = True
