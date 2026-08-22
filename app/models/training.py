"""Training modules model"""

from sqlalchemy import Column, String, Integer, Text, JSON, Boolean
from app.models.base import BaseModel


class TrainingModule(BaseModel):
    """Structured training paths for enterprises"""

    __tablename__ = "training_modules"

    enterprise = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(20), default="marathi", nullable=False)

    # Content
    content = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)

    # Structure
    sequence = Column(Integer, default=0, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), default="beginner", nullable=False)

    # Resources
    resources = Column(JSON, default=[], nullable=False)
    practical_exercises = Column(JSON, default=[], nullable=False)

    # Metadata
    is_published = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<TrainingModule(id={self.id}, enterprise={self.enterprise}, title={self.title})>"
