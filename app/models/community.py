"""Community discussion models"""

from sqlalchemy import Column, String, Integer, Text, JSON, Boolean, ForeignKey
from app.models.base import BaseModel


class CommunityPost(BaseModel):
    """Community posts and discussions"""

    __tablename__ = "community_posts"

    author_farmer_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(20), default="marathi", nullable=False)

    # Engagement
    view_count = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)

    # Status
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)

    # Tags and Topics
    tags = Column(JSON, default=[], nullable=False)
    mentioned_enterprises = Column(JSON, default=[], nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<CommunityPost(id={self.id}, title={self.title}, category={self.category})>"


class CommunityComment(BaseModel):
    """Comments on community posts"""

    __tablename__ = "community_comments"

    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    author_farmer_id = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    language = Column(String(20), default="marathi", nullable=False)

    # Engagement
    helpful_count = Column(Integer, default=0, nullable=False)

    # Status
    is_published = Column(Boolean, default=True, nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<CommunityComment(id={self.id}, post_id={self.post_id})>"
