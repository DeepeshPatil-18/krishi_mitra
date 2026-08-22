"""Expert and expert request models"""

from sqlalchemy import Column, String, Integer, Text, JSON, Boolean, ForeignKey
from app.models.base import BaseModel


class Expert(BaseModel):
    """Domain experts"""

    __tablename__ = "experts"

    name = Column(String(255), nullable=False)
    expertise = Column(JSON, default=[], nullable=False)
    languages = Column(JSON, default=["english"], nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    availability_status = Column(String(20), default="available", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Expert(id={self.id}, name={self.name})>"


class ExpertRequest(BaseModel):
    """Farmer requests to expert"""

    __tablename__ = "expert_requests"

    farmer_id = Column(String(50), nullable=False, index=True)
    expert_id = Column(Integer, ForeignKey("experts.id"), nullable=True)
    category = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    context = Column(JSON, default={}, nullable=False)

    # Status Workflow
    status = Column(String(20), default="pending", nullable=False)  # pending, assigned, resolved, closed
    priority = Column(String(20), default="normal", nullable=False)  # low, normal, high

    # Response
    response = Column(Text, nullable=True)
    response_date = Column(String(20), nullable=True)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<ExpertRequest(id={self.id}, farmer_id={self.farmer_id}, status={self.status})>"
