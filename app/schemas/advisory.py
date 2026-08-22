"""Advisory and recommendation schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class FarmerContext(BaseModel):
    """Comprehensive farmer context for advisory"""
    
    # Core information
    budget_rupees: int = Field(..., gt=0)
    location: Optional[str] = Field(None, description="State or region")
    land_size_hectares: Optional[float] = Field(None, ge=0.0)
    water_availability: Optional[str] = Field(None, description="low, medium, high")
    experience_level: str = Field(default="beginner", pattern="^(beginner|intermediate|expert)$")
    
    # Additional context
    income_goal_monthly: Optional[int] = Field(None, gt=0)
    preferred_enterprise: Optional[str] = Field(None, description="Enterprise code if preferred")
    existing_resources: Optional[List[str]] = Field(None, description="e.g., [\"land\", \"livestock\", \"shed\"]")
    electricity_available: Optional[bool] = Field(None)
    willingness_to_learn: Optional[bool] = Field(default=True)
    risk_tolerance: Optional[str] = Field(default="medium", pattern="^(low|medium|high)$")
    time_availability: Optional[str] = Field(None, description="full_time, part_time, limited")


class AdvisoryRequest(BaseModel):
    """Request for advisory/recommendation"""

    farmer_id: str = Field(..., min_length=1)
    language: str = Field(default="marathi", pattern="^(marathi|hindi|english)$")
    
    # Backward compatible simple fields
    budget_rupees: Optional[int] = Field(None)
    land_size_hectares: Optional[float] = Field(None)
    location: Optional[str] = Field(None)
    experience_level: Optional[str] = Field(None)
    
    # Or detailed farmer context
    farmer_context: Optional[FarmerContext] = Field(None)


class FactorScoreDetail(BaseModel):
    """Detailed score for a single factor"""
    factor: str
    score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    positive_indicators: List[str]
    negative_indicators: List[str]
    missing_data: List[str]


class RecommendedEnterprise(BaseModel):
    """A recommended enterprise with detailed scoring"""

    enterprise_code: str
    enterprise_name: str
    suitability_score: float = Field(..., ge=0.0, le=100.0)
    
    # Score breakdown
    factor_scores: Dict[str, FactorScoreDetail] = Field(default_factory=dict)
    primary_positive_factors: List[str] = Field(default_factory=list)
    primary_negative_factors: List[str] = Field(default_factory=list)
    
    # Practical information
    estimated_investment_min: int
    estimated_investment_max: Optional[int] = None
    requirements: List[str]
    risks: List[str]
    
    # Connections
    training_recommendations: List[str]
    relevant_schemes: List[str]
    potential_markets: List[str]
    
    # Guidance
    next_actions: List[str]
    why_ranked_higher: Optional[str] = Field(None, description="Why this is better than alternatives")


class AdvisoryResponse(BaseModel):
    """Advisory response with recommendations"""

    farmer_id: str
    language: str
    recommendations: List[RecommendedEnterprise]
    
    # Quality indicators
    information_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness of farmer data (0-1)")
    missing_information: List[str] = Field(default_factory=list)
    
    # Summary
    summary: str
    next_steps: List[str]
    
    # Additional context
    recommendation_confidence: Optional[str] = Field(None, description="low, medium, high - based on data completeness")
    resources: Optional[List[Dict[str, Any]]] = None
