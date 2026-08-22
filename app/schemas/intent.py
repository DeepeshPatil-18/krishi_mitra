"""Intent detection schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class Intent(str, Enum):
    """Intent types"""

    LIVELIHOOD_RECOMMENDATION = "livelihood_recommendation"
    SCHEME_SEARCH = "scheme_search"
    TRAINING_REQUEST = "training_request"
    MARKET_SEARCH = "market_search"
    EXPERT_REQUEST = "expert_request"
    GENERAL_QUESTION = "general_question"
    COMMUNITY = "community"


class IntentRequest(BaseModel):
    """Intent detection request"""

    farmer_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    language: str = Field(default="marathi", pattern="^(marathi|hindi|english)$")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class IntentResponse(BaseModel):
    """Intent detection response"""

    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None
