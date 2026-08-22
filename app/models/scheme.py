"""Government scheme model"""

from sqlalchemy import Column, String, Integer, Text, JSON, Boolean
from app.models.base import BaseModel


class Scheme(BaseModel):
    """Government agricultural schemes"""

    __tablename__ = "schemes"

    name = Column(String(255), nullable=False, index=True)
    department = Column(String(255), nullable=False)
    state = Column(String(50), nullable=False)
    enterprise = Column(String(100), nullable=False)

    # Scheme Details
    description = Column(Text, nullable=True)
    subsidy_percentage = Column(Integer, nullable=True)
    subsidy_amount_rupees = Column(Integer, nullable=True)

    # Eligibility
    eligibility_criteria = Column(JSON, default=[], nullable=False)
    required_documents = Column(JSON, default=[], nullable=False)

    # Process
    application_process = Column(Text, nullable=True)
    application_deadline = Column(String(100), nullable=True)
    processing_time_days = Column(Integer, nullable=True)

    # Reference
    official_source_url = Column(String(500), nullable=True)
    last_verified_date = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Additional
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Scheme(id={self.id}, name={self.name}, state={self.state})>"
