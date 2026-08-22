"""Scheme-related schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SchemeResponse(BaseModel):
    """Government scheme response"""

    id: int
    name: str
    department: str
    state: str
    enterprise: str
    description: Optional[str]
    subsidy_percentage: Optional[int]
    subsidy_amount_rupees: Optional[int]
    eligibility_criteria: List[str]
    required_documents: List[str]
    application_process: Optional[str]
    application_deadline: Optional[str]
    processing_time_days: Optional[int]
    official_source_url: Optional[str]
    last_verified_date: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
