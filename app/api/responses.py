"""Common API response models and error handling"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorCode(str, Enum):
    """API error codes"""
    INVALID_REQUEST = "invalid_request"
    MISSING_FIELD = "missing_field"
    INVALID_LANGUAGE = "invalid_language"
    INVALID_BUDGET = "invalid_budget"
    EMPTY_MESSAGE = "empty_message"
    SERVICE_ERROR = "service_error"
    AI_UNAVAILABLE = "ai_unavailable"
    NOT_IMPLEMENTED = "not_implemented"


class APIError(BaseModel):
    """Standard API error response"""
    error: str = Field(..., description="Error message")
    error_code: ErrorCode = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Generic success response wrapper"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class IntentDetectionResponse(BaseModel):
    """Response from intent detection endpoint"""
    intent: str = Field(..., description="Detected intent type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters")
    detected_language: Optional[str] = Field(None, description="Detected language")
    reasoning: Optional[str] = Field(None, description="Explanation of detection")


class AdvisoryRecommendationResponse(BaseModel):
    """Response from advisory recommendation endpoint"""
    farmer_budget: int = Field(..., description="Farmer's budget in rupees")
    farmer_land: float = Field(..., description="Farmer's available land in hectares")
    recommendations: List[Dict[str, Any]] = Field(..., description="List of recommendations")
    summary: str = Field(..., description="Summary of recommendations")


class AssistantMessageResponse(BaseModel):
    """Response from assistant chat endpoint"""
    intent: str = Field(..., description="Intent of user message")
    response: str = Field(..., description="Assistant response")
    response_type: str = Field(..., description="Type of response (text, advisory, info, etc.)")
    requires_further_input: bool = Field(False, description="Whether more info is needed")
    suggested_next_action: Optional[str] = Field(None, description="Suggested next action")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
