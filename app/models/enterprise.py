"""Enterprise/Allied business model"""

from sqlalchemy import Column, String, Integer, Text, JSON, Float
from app.models.base import BaseModel


class Enterprise(BaseModel):
    """Allied agricultural enterprises"""

    __tablename__ = "enterprises"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name_en = Column(String(255), nullable=False)
    name_hi = Column(String(255), nullable=False)
    name_mr = Column(String(255), nullable=False)

    # Description
    description = Column(Text, nullable=True)

    # Suitability Parameters
    min_budget_rupees = Column(Integer, default=0, nullable=False)
    max_budget_rupees = Column(Integer, nullable=True)
    min_land_hectares = Column(Float, default=0.0, nullable=False)
    max_land_hectares = Column(Float, nullable=True)
    space_requirement = Column(String(255), nullable=True)  # e.g., "indoor", "outdoor", "any"

    # Resource Requirements
    water_requirement = Column(String(255), nullable=True)  # "high", "medium", "low"
    climate_suitable = Column(JSON, default=[], nullable=False)

    # Investment Details
    estimated_investment = Column(Integer, nullable=True)
    estimated_income_monthly = Column(Integer, nullable=True)
    payback_period_months = Column(Integer, nullable=True)

    # Risk Factors
    risk_factors = Column(JSON, default=[], nullable=False)
    requirements = Column(JSON, default=[], nullable=False)

    # Training and Support
    training_path = Column(String(50), nullable=True)
    support_level = Column(String(20), default="high", nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Enterprise(id={self.id}, code={self.code}, name_en={self.name_en})>"
