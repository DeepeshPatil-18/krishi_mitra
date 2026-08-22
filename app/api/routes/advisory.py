"""Advisory API routes"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.services.advisory_service import AdvisoryService
from app.services.advisory_engine_v2 import AdvisoryEngineV2
from app.schemas.advisory import AdvisoryRequest, FarmerContext
from app.api.responses import (
    APIError, 
    ErrorCode
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/advisory", tags=["advisory"])


@router.post("/recommend")
async def get_recommendations(
    request: AdvisoryRequest = Body(...)
) -> Dict[str, Any]:
    """
    Get personalized livelihood recommendations using Advisory Engine V2.
    
    Supports both simplified and detailed farmer context.
    
    Simple mode:
    - budget_rupees (required)
    - land_size_hectares
    - experience_level
    
    Detailed mode:
    - farmer_context with complete information
    
    Returns ranked recommendations with detailed scoring breakdown.
    """
    
    # Validate input
    if request.budget_rupees <= 0:
        raise HTTPException(
            status_code=400,
            detail=APIError(
                error="Budget must be greater than 0",
                error_code=ErrorCode.INVALID_BUDGET,
                details={"field": "budget_rupees", "provided": request.budget_rupees}
            ).dict()
        )
    
    try:
        # Build farmer context from request
        if request.farmer_context:
            # Use provided detailed context
            context = request.farmer_context
        else:
            # Build from simple fields
            context = FarmerContext(
                budget_rupees=request.budget_rupees,
                land_size_hectares=request.land_size_hectares,
                location=request.location,
                experience_level=request.experience_level or "beginner"
            )
        
        # Get recommendations using Advisory Engine V2
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        # Calculate information completeness
        missing_info = AdvisoryEngineV2._get_missing_information(context)
        information_completeness = (
            recommendations[0].factor_scores.get("budget_fit", {}).get("weight", 0)
            if recommendations and recommendations[0].factor_scores
            else 0.5
        )
        
        # Calculate from factor_scores if available
        if recommendations and recommendations[0].factor_scores:
            missing_count = sum(
                len(score.get("missing_data", []))
                for score in recommendations[0].factor_scores.values()
            )
            information_completeness = max(0.3, 1.0 - (missing_count * 0.15))
        
        # Generate confidence level
        if information_completeness >= 0.8:
            confidence = "high"
        elif information_completeness >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate summary
        if recommendations:
            top_rec = recommendations[0]
            summary = (
                f"Based on your context, {top_rec.enterprise_name} is your best option "
                f"(score: {top_rec.suitability_score:.0f}/100). "
            )
            
            if top_rec.why_ranked_higher:
                summary += top_rec.why_ranked_higher
            else:
                summary += f"It matches your budget and experience level well."
            
            if information_completeness < 0.7:
                summary += f"\n\nProviding more information (land size, water availability, goals) would improve the recommendation."
        else:
            summary = "Unable to generate recommendations with provided information."
        
        return {
            "farmer_id": request.farmer_id,
            "language": request.language,
            "recommendations": [
                rec.dict() for rec in recommendations
            ],
            "information_completeness": round(information_completeness, 2),
            "missing_information": missing_info,
            "summary": summary,
            "next_steps": (
                recommendations[0].next_actions if recommendations
                else ["Provide more information for better recommendations"]
            ),
            "recommendation_confidence": confidence
        }
    
    except Exception as e:
        logger.error(f"Advisory recommendation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error="Failed to generate recommendations",
                error_code=ErrorCode.SERVICE_ERROR,
                details={"error": str(e)}
            ).dict()
        )


@router.get("/enterprises/{enterprise_code}")
async def get_enterprise_details(enterprise_code: str):
    """
    Get detailed information about a specific enterprise
    
    Returns comprehensive information including:
    - Description
    - Budget and land requirements
    - Investment and income estimates
    - Resource requirements
    - Risk factors
    - Available training
    - Market opportunities
    """
    try:
        enterprise = AdvisoryService.get_enterprise_details(enterprise_code)
        
        if not enterprise:
            raise HTTPException(
                status_code=404,
                detail=APIError(
                    error=f"Enterprise not found: {enterprise_code}",
                    error_code=ErrorCode.INVALID_REQUEST,
                    details={"enterprise_code": enterprise_code}
                ).dict()
            )
        
        return {
            "success": True,
            "data": enterprise
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching enterprise details: {e}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error="Failed to fetch enterprise details",
                error_code=ErrorCode.SERVICE_ERROR,
                details={"error": str(e)}
            ).dict()
        )


@router.get("/schemes/{enterprise_code}")
async def get_relevant_schemes(enterprise_code: str, state: str = "maharashtra"):
    """
    Get government schemes applicable to an enterprise
    
    Returns available schemes with:
    - Subsidy amounts and percentages
    - Eligibility criteria
    - Required documents
    - Application process
    - Processing timelines
    """
    try:
        schemes = AdvisoryService.get_schemes_for_enterprise(enterprise_code, state)
        
        return {
            "success": True,
            "enterprise": enterprise_code,
            "state": state,
            "schemes": schemes
        }
    
    except Exception as e:
        logger.error(f"Error fetching schemes: {e}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error="Failed to fetch schemes",
                error_code=ErrorCode.SERVICE_ERROR,
                details={"error": str(e)}
            ).dict()
        )
