"""Intent detection API routes"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import logging

from app.schemas.intent import IntentRequest
from app.services.intent_router import IntentRouter
from app.services.language_service import LanguageService
from app.api.responses import IntentDetectionResponse, APIError, ErrorCode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/intent", tags=["intent"])


@router.post("/detect", response_model=IntentDetectionResponse)
async def detect_intent(request: IntentRequest) -> IntentDetectionResponse:
    """
    Detect intent from farmer message
    
    Supported intents:
    - livelihood_recommendation: Farm business recommendations
    - scheme_search: Government schemes
    - training_request: Training and guidance
    - market_search: Market and buyer information
    - expert_request: Request expert assistance
    - general_question: General agricultural question
    - community: Community discussions
    
    Supported languages:
    - english
    - hindi (hi)
    - marathi (mr)
    """
    
    # Validate input
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail=APIError(
                error="Message cannot be empty",
                error_code=ErrorCode.EMPTY_MESSAGE,
                details={"field": "message"}
            ).dict()
        )
    
    # Auto-detect language if not provided
    detected_language = request.language
    if not detected_language or detected_language == "auto":
        detected_language = LanguageService.detect_language(request.message)
        if not LanguageService.validate_language(detected_language):
            detected_language = "english"
    
    # Validate language
    if not LanguageService.validate_language(detected_language):
        raise HTTPException(
            status_code=400,
            detail=APIError(
                error=f"Unsupported language: {detected_language}",
                error_code=ErrorCode.INVALID_LANGUAGE,
                details={"supported": ["english", "hindi", "marathi"], "provided": detected_language}
            ).dict()
        )
    
    try:
        # Detect intent using existing intent router
        intent, confidence, extracted_params = IntentRouter.detect_intent(
            message=request.message,
            language=detected_language,
            context=request.context
        )
        
        # Extract additional parameters if available
        extracted_params.update(
            IntentRouter.extract_parameters(
                request.message,
                intent,
                detected_language
            )
        )
        
        return IntentDetectionResponse(
            intent=intent.value,
            confidence=confidence,
            extracted_parameters=extracted_params,
            detected_language=detected_language,
            reasoning=f"Detected {intent.value} with confidence {confidence:.2f}"
        )
    
    except Exception as e:
        logger.error(f"Intent detection error: {e}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error="Failed to detect intent",
                error_code=ErrorCode.SERVICE_ERROR,
                details={"error": str(e)}
            ).dict()
        )
