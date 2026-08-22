"""Assistant API routes - main chat interface using AI Orchestrator"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.services.ai_orchestrator import AIOrchestrator, CapabilityStatus
from app.services.response_grounder import ResponseGrounder, GroundingContext
from app.services.language_service import LanguageService
from app.services.krishimitra_prompts import KrishiMitraPrompts
from app.api.responses import (
    APIError,
    ErrorCode
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


class AssistantRequest(BaseModel):
    """Assistant chat request"""
    message: str = Field(..., min_length=1, description="User message")
    language: Optional[str] = Field(default="auto", description="Language (auto, english, hindi, marathi)")
    farmer_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional farmer context (budget, land, experience, etc.)"
    )
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class AssistantResponse(BaseModel):
    """Assistant chat response"""
    intent: str
    response: str
    response_type: str
    detected_language: str
    information_completeness: float = 1.0
    missing_information: Optional[list] = None
    requires_further_input: bool = False
    suggested_next_action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=AssistantResponse)
async def chat(request: AssistantRequest = Body(...)) -> AssistantResponse:
    """
    Main assistant endpoint for farmer queries using AI Orchestrator.
    
    Pipeline:
    1. Orchestrate: detect language, intent, extract entities
    2. Execute: call appropriate backend capability
    3. Ground: ensure response is grounded in backend data
    4. Generate: create farmer-friendly response
    
    Example queries:
    - English: "I have 50000 rupees. What business can I start?"
    - Hindi: "मेरे पास पचास हजार रुपये हैं। मैं क्या शुरू कर सकता हूँ?"
    - Marathi: "माझ्याकडे पन्नास हजार रुपये आहेत. मी काय सुरू करू?"
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
    
    try:
        # STEP 1: ORCHESTRATE
        # Detects language, intent, extracts entities, builds context
        logger.info(f"Orchestrating: {request.message[:50]}...")
        
        orch_ctx = AIOrchestrator.orchestrate(
            message=request.message,
            language=request.language,
            provided_context=request.farmer_context,
        )
        
        logger.info(
            f"Orchestrated: intent={orch_ctx.intent.value}, "
            f"language={orch_ctx.detected_language}, "
            f"completeness={orch_ctx.information_completeness:.2f}"
        )
        
        # STEP 2: EXECUTE
        # Call the appropriate backend capability
        logger.info(f"Executing capability for intent: {orch_ctx.intent.value}")
        
        capability_result = AIOrchestrator.execute_capability(orch_ctx)
        
        # STEP 3: GROUND
        # Ensure response is grounded in backend data
        grounding_ctx = GroundingContext(
            backend_result=capability_result,
            structured_data=capability_result.data,
            language=orch_ctx.detected_language,
            farmer_budget=orch_ctx.farmer_context.budget_rupees if orch_ctx.farmer_context else None,
            farmer_location=orch_ctx.farmer_context.location if orch_ctx.farmer_context else None,
            missing_information=orch_ctx.missing_information,
            information_completeness=orch_ctx.information_completeness,
        )
        
        # STEP 4: GENERATE RESPONSE
        # Create farmer-friendly response
        response_text = _generate_response(
            orch_ctx=orch_ctx,
            capability_result=capability_result,
            grounding_ctx=grounding_ctx,
        )
        
        # Determine response type
        response_type = _get_response_type(orch_ctx.intent)
        
        return AssistantResponse(
            intent=orch_ctx.intent.value,
            response=response_text,
            response_type=response_type,
            detected_language=orch_ctx.detected_language,
            information_completeness=orch_ctx.information_completeness,
            missing_information=orch_ctx.missing_information if orch_ctx.missing_information else None,
            requires_further_input=len(orch_ctx.missing_information) > 0,
            suggested_next_action=_get_next_action(orch_ctx.intent),
            metadata={
                "intent_confidence": orch_ctx.intent_confidence,
                "capability_status": capability_result.status.value,
                "extracted_entities": orch_ctx.extracted_entities,
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assistant error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error="Assistant encountered an error",
                error_code=ErrorCode.SERVICE_ERROR,
                details={"error": str(e)}
            ).dict()
        )


def _generate_response(
    orch_ctx,
    capability_result,
    grounding_ctx: GroundingContext,
) -> str:
    """Generate farmer-friendly response"""
    
    from app.schemas.intent import Intent
    
    if capability_result.status == CapabilityStatus.NOT_IMPLEMENTED:
        # Capability not implemented yet
        return capability_result.message or (
            "This capability is not yet available. "
            "Please try asking about something else, like livelihood recommendations, "
            "schemes, training, or market opportunities."
        )
    
    if capability_result.error:
        # Error occurred
        logger.warning(f"Capability error: {capability_result.error}")
        return _get_error_message(orch_ctx.intent, orch_ctx.detected_language)
    
    if not capability_result.data:
        # No data returned
        return _get_no_data_message(orch_ctx.intent, orch_ctx.detected_language)
    
    # Generate appropriate response based on intent
    if orch_ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION:
        return _format_advisory_response(
            capability_result.data,
            orch_ctx.detected_language,
            orch_ctx.information_completeness,
        )
    
    elif orch_ctx.intent == Intent.SCHEME_SEARCH:
        return _format_scheme_response(
            capability_result.data,
            orch_ctx.detected_language,
        )
    
    elif orch_ctx.intent == Intent.TRAINING_REQUEST:
        return _format_training_response(
            capability_result.data,
            orch_ctx.detected_language,
        )
    
    elif orch_ctx.intent == Intent.MARKET_SEARCH:
        return _format_market_response(
            capability_result.data,
            orch_ctx.detected_language,
        )
    
    elif orch_ctx.intent == Intent.GENERAL_QUESTION:
        return _format_general_response(
            orch_ctx.message,
            orch_ctx.detected_language,
        )
    
    else:
        return "Thank you for your question. Our team is working to help you."


def _format_advisory_response(
    data: Dict[str, Any],
    language: str,
    completeness: float,
) -> str:
    """Format advisory response"""
    recommendations = data.get("recommendations", [])
    
    if not recommendations:
        if language == "marathi":
            return "तुमच्या माहितीच्या आधारावर सुपारिश करणे कठीण दिसते. कृपया तुमच्या बजेट, जमीन आणि अनुभवाबद्दल अधिक सांगा."
        elif language == "hindi":
            return "आपकी जानकारी के आधार पर सिफारिश करना मुश्किल लग रहा है। कृपया अपने बजट, भूमि और अनुभव के बारे में अधिक बताएं।"
        else:
            return "I need more information to make a good recommendation. Please share details about your budget, available land, and farming experience."
    
    top = recommendations[0]
    enterprise = top.get("enterprise_name", "this enterprise")
    score = top.get("suitability_score", 0)
    investment = top.get("estimated_investment_min")
    factors = top.get("primary_positive_factors", [])[:2]
    
    if language == "marathi":
        msg = f"तुमच्या स्थितीनुसार मी शिफारस करते: {enterprise}\n"
        msg += f"उपयुक्ततेचे गुण: {score:.0f}/100\n\n"
        if factors:
            msg += "कारण:\n"
            for factor in factors:
                msg += f"• {factor}\n"
        if investment:
            msg += f"\nअंदाजे गुंतवणूक: ₹{investment:,}\n"
        if completeness < 0.7:
            msg += f"\nतुम्ही आपली उत्पन्नाची लक्ष्य आणि वेळेची उपलब्धता सांगितल्यास मी अधिक चांगली सुपारिश देऊ शकेन."
    elif language == "hindi":
        msg = f"आपकी स्थिति के अनुसार मैं सुझाव देता हूं: {enterprise}\n"
        msg += f"उपयुक्तता स्कोर: {score:.0f}/100\n\n"
        if factors:
            msg += "कारण:\n"
            for factor in factors:
                msg += f"• {factor}\n"
        if investment:
            msg += f"\nअनुमानित निवेश: ₹{investment:,}\n"
        if completeness < 0.7:
            msg += f"\nअगर आप अपने आय लक्ष्य और समय की उपलब्धता बताएं तो मैं बेहतर सुझाव दे सकता हूं।"
    else:
        msg = f"Based on your situation, I recommend: {enterprise}\n"
        msg += f"Suitability Score: {score:.0f}/100\n\n"
        if factors:
            msg += "Why this works for you:\n"
            for factor in factors:
                msg += f"• {factor}\n"
        if investment:
            msg += f"\nEstimated investment: ₹{investment:,}\n"
        if completeness < 0.7:
            msg += f"\nIf you share your monthly income goal and time availability, I can give you a better recommendation."
    
    return msg


def _format_scheme_response(
    data: Dict[str, Any],
    language: str,
) -> str:
    """Format scheme search response"""
    schemes = data.get("schemes", [])
    
    if not schemes:
        if language == "marathi":
            return "सध्या या क्षेत्रासाठी कोणते विशेष योजना उपलब्ध आहेत याची माहिती नाही. कृपया तुमच्या स्थानिक कृषि विभागाशी संपर्क साधा."
        elif language == "hindi":
            return "इस क्षेत्र के लिए उपलब्ध योजनाओं की जानकारी नहीं है। कृपया अपने स्थानीय कृषि विभाग से संपर्क करें।"
        else:
            return "I don't have specific scheme information for your area. Please contact your local agriculture department for available government support."
    
    if language == "marathi":
        msg = f"तुमच्या क्षेत्रासाठी {len(schemes)} योजना उपलब्ध आहेत:\n\n"
        for scheme in schemes[:3]:
            msg += f"• {scheme.get('name', 'Scheme')}\n"
    elif language == "hindi":
        msg = f"आपके क्षेत्र के लिए {len(schemes)} योजनाएं उपलब्ध हैं:\n\n"
        for scheme in schemes[:3]:
            msg += f"• {scheme.get('name', 'Scheme')}\n"
    else:
        msg = f"I found {len(schemes)} available schemes for your area:\n\n"
        for scheme in schemes[:3]:
            msg += f"• {scheme.get('name', 'Scheme')}\n"
    
    if language == "marathi":
        msg += "\nअधिक माहितीसाठी तुमच्या स्थानिक कृषि अधिकारांशी किंवा योजना केंद्रांशी संपर्क साधा."
    elif language == "hindi":
        msg += "\nअधिक जानकारी के लिए अपने स्थानीय कृषि अधिकारियों या योजना केंद्रों से संपर्क करें।"
    else:
        msg += "\nFor detailed eligibility and application, contact your local agriculture office or scheme center."
    
    return msg


def _format_training_response(
    data: Dict[str, Any],
    language: str,
) -> str:
    """Format training response"""
    training = data.get("training_modules", [])
    
    if not training:
        if language == "marathi":
            return "प्रशिक्षण सामग्री शीघ्रच उपलब्ध होईल. कृपया पुन्हा प्रयत्न करा."
        elif language == "hindi":
            return "प्रशिक्षण सामग्री जल्द उपलब्ध होगी। कृपया बाद में फिर से प्रयास करें।"
        else:
            return "Training materials will be available soon. Please check back later."
    
    if language == "marathi":
        msg = f"उपलब्ध प्रशिक्षण मॉड्यूल:\n\n"
        for module in training[:3]:
            msg += f"• {module.get('title', 'Module')}\n"
    elif language == "hindi":
        msg = f"उपलब्ध प्रशिक्षण मॉड्यूल:\n\n"
        for module in training[:3]:
            msg += f"• {module.get('title', 'Module')}\n"
    else:
        msg = f"Available training modules:\n\n"
        for module in training[:3]:
            msg += f"• {module.get('title', 'Module')}\n"
    
    if language == "marathi":
        msg += "\nप्रशिक्षण सुरू करण्यासाठी, कृपया आमच्या समर्थन दलाशी संपर्क साधा."
    elif language == "hindi":
        msg += "\nप्रशिक्षण शुरू करने के लिए, कृपया हमारी सहायता टीम से संपर्क करें।"
    else:
        msg += "\nTo start training, please contact our support team."
    
    return msg


def _format_market_response(
    data: Dict[str, Any],
    language: str,
) -> str:
    """Format market search response"""
    markets = data.get("markets", [])
    
    if not markets:
        if language == "marathi":
            return "तुमच्या क्षेत्रासाठी बाजार माहिती सध्या मर्यादित आहे. आमचा समर्थन दल तुम्हाला सहायता करू शकतो."
        elif language == "hindi":
            return "आपके क्षेत्र के लिए बाजार जानकारी अभी सीमित है। हमारी सहायता टीम आपकी मदद कर सकती है।"
        else:
            return "Market information for your area is currently limited. Our support team can help you connect."
    
    if language == "marathi":
        msg = f"तुमच्या क्षेत्रातील {len(markets)} बाजार संधी:\n\n"
        for market in markets[:3]:
            msg += f"• {market.get('location', 'Market')}\n"
    elif language == "hindi":
        msg = f"आपके क्षेत्र में {len(markets)} बाजार के अवसर:\n\n"
        for market in markets[:3]:
            msg += f"• {market.get('location', 'Market')}\n"
    else:
        msg = f"Market opportunities in your area ({len(markets)} found):\n\n"
        for market in markets[:3]:
            msg += f"• {market.get('location', 'Market')}\n"
    
    return msg


def _format_general_response(
    message: str,
    language: str,
) -> str:
    """Format general question response"""
    if language == "marathi":
        return (
            "मी तुम्हाला कृषी जीविकेच्या योजनेत मदत करू शकते. तुम्ही माझ्याला विचारू शकता:\n"
            "• तुमच्या परिस्थितीनुसार व्यवसाय शिफारश\n"
            "• सरकारी योजना आणि सब्सिडी\n"
            "• प्रशिक्षण आणि मार्गदर्शन\n"
            "• बाजार संधी\n"
            "• तज्ञ सहायता\n\n"
            "तुम्ही आज मला कसे मदत करू शकते?"
        )
    elif language == "hindi":
        return (
            "मैं आपको कृषि आजीविका योजना में मदद कर सकता हूं। आप मुझसे पूछ सकते हैं:\n"
            "• आपकी स्थिति के आधार पर व्यवसाय की सिफारिश\n"
            "• सरकारी योजनाएं और सब्सिडी\n"
            "• प्रशिक्षण और मार्गदर्शन\n"
            "• बाजार के अवसर\n"
            "• विशेषज्ञ सहायता\n\n"
            "आज मैं आपकी कैसे मदद कर सकता हूं?"
        )
    else:
        return (
            "I'm here to help with agricultural livelihood planning. You can ask me about:\n"
            "• Business recommendations based on your situation\n"
            "• Government schemes and subsidies\n"
            "• Training and guidance\n"
            "• Market opportunities\n"
            "• Expert assistance\n\n"
            "How can I help you today?"
        )


def _get_error_message(intent, language: str) -> str:
    """Get error message for failed capability"""
    if language == "marathi":
        return "खेद आहे. काहीतरी चुकले आहे. कृपया पुन्हा प्रयत्न करा किंवा आमच्या समर्थन दलाशी संपर्क साधा."
    elif language == "hindi":
        return "खेद है। कुछ गलत हुआ। कृपया फिर से प्रयास करें या हमारी सहायता टीम से संपर्क करें।"
    else:
        return "Sorry, something went wrong. Please try again or contact our support team."


def _get_no_data_message(intent, language: str) -> str:
    """Get message for when no data is available"""
    if language == "marathi":
        return "या क्षेत्रातील माहिती सध्या उपलब्ध नाही. कृपया पुन्हा प्रयत्न करा."
    elif language == "hindi":
        return "इस क्षेत्र की जानकारी अभी उपलब्ध नहीं है। कृपया फिर से प्रयास करें।"
    else:
        return "Information for this area is not yet available. Please try again later."


def _get_response_type(intent) -> str:
    """Get response type based on intent"""
    from app.schemas.intent import Intent
    
    if intent == Intent.LIVELIHOOD_RECOMMENDATION:
        return "advisory"
    elif intent == Intent.SCHEME_SEARCH:
        return "schemes"
    elif intent == Intent.TRAINING_REQUEST:
        return "training"
    elif intent == Intent.MARKET_SEARCH:
        return "market"
    elif intent == Intent.EXPERT_REQUEST:
        return "expert"
    elif intent == Intent.COMMUNITY:
        return "community"
    else:
        return "general"


def _get_next_action(intent) -> str:
    """Get suggested next action based on intent"""
    from app.schemas.intent import Intent
    
    if intent == Intent.LIVELIHOOD_RECOMMENDATION:
        return "Would you like to know about training or government schemes for this enterprise?"
    elif intent == Intent.SCHEME_SEARCH:
        return "Would you like information about training programs?"
    elif intent == Intent.TRAINING_REQUEST:
        return "Ready to start learning?"
    elif intent == Intent.MARKET_SEARCH:
        return "Would you like help finding buyers in your area?"
    else:
        return None
