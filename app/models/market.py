"""Market and buyer model"""

from sqlalchemy import Column, String, Integer, Text, JSON, Float, Boolean
from app.models.base import BaseModel


class Market(BaseModel):
    """Market opportunities and buyers"""

    __tablename__ = "markets"

    product = Column(String(255), nullable=False, index=True)
    enterprise = Column(String(100), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    buyer_name = Column(String(255), nullable=True)
    buyer_type = Column(String(50), nullable=False)  # retail, wholesale, processor, exporter, etc.

    # Market Details
    price_per_unit = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    unit_type = Column(String(50), nullable=True)  # kg, liter, piece, dozen, etc.
    price_last_updated = Column(String(20), nullable=True)

    # Buyer Information
    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    # Logistics
    can_arrange_logistics = Column(Boolean, default=False, nullable=False)
    min_purchase_quantity = Column(Float, nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_source = Column(String(255), nullable=True)
    is_prototype_data = Column(Boolean, default=False, nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Market(id={self.id}, product={self.product}, location={self.location})>"
