"""Expert request schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ExpertRequestCreate(BaseModel):
    """Create an expert request"""

    farmer_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    language: str = Field(default="marathi", pattern="^(marathi|hindi|english)$")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ExpertRequestResponse(BaseModel):
    """Expert request response"""

    id: int
    farmer_id: str
    expert_id: Optional[int]
    category: str
    question: str
    status: str
    priority: str
    response: Optional[str]
    response_date: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
