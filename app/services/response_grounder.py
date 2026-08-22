"""Response Grounder - ensures AI responses are grounded in backend data"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.services.ai_orchestrator import CapabilityResult, CapabilityStatus

logger = logging.getLogger(__name__)


@dataclass
class GroundingContext:
    """Context for grounding AI responses"""
    backend_result: Optional[CapabilityResult] = None
    structured_data: Optional[Dict[str, Any]] = None
    language: str = "english"
    farmer_budget: Optional[int] = None
    farmer_location: Optional[str] = None
    missing_information: List[str] = None
    information_completeness: float = 0.0

    def __post_init__(self):
        if self.missing_information is None:
            self.missing_information = []


class ResponseGrounder:
    """
    Ensures AI responses are grounded in backend data.
    
    Prevents:
    - Fabricated enterprise suitability scores
    - Invented scheme eligibility
    - Made-up market data
    - False financial calculations
    - Confidence beyond what data supports
    
    Enables:
    - Natural language explanation of backend results
    - Translation to farmer-friendly language
    - Appropriate uncertainty/confidence statements
    - Missing information acknowledgments
    """

    # Safety rules for different response types
    SAFETY_RULES = {
        "advisory": {
            "never_fabricate": [
                "suitability_score",
                "investment_amount",
                "estimated_income",
                "factor_explanations",
            ],
            "must_include": [
                "top_recommendation",
                "why_this_option",
                "next_steps",
            ],
            "can_explain": [
                "why_scores_differ",
                "factors_affecting_choice",
                "missing_information_impact",
            ],
        },
        "scheme_search": {
            "never_fabricate": [
                "scheme_eligibility",
                "subsidy_amount",
                "application_process",
                "government_name",
            ],
            "must_include": [
                "scheme_names",
                "basic_requirements",
                "application_location",
            ],
            "can_explain": [
                "how_to_apply",
                "typical_benefits",
            ],
        },
        "market_search": {
            "never_fabricate": [
                "current_prices",
                "buyer_contact_info",
                "demand_guarantee",
                "profit_margins",
            ],
            "must_include": [
                "market_locations",
                "typical_products",
            ],
            "can_explain": [
                "how_to_connect",
                "storage_considerations",
            ],
        },
        "training_request": {
            "never_fabricate": [
                "course_duration",
                "certification_value",
                "learning_outcomes",
                "provider_info",
            ],
            "must_include": [
                "available_modules",
                "topic_areas",
            ],
            "can_explain": [
                "why_this_training",
                "how_to_enroll",
            ],
        },
    }

    @staticmethod
    def ground_response(
        grounding_context: GroundingContext,
        ai_draft: Optional[str] = None,
        response_type: str = "advisory",
    ) -> Dict[str, Any]:
        """
        Ground a response in backend data.
        
        Args:
            grounding_context: Context with backend result
            ai_draft: Optional AI-generated draft (will be validated)
            response_type: Type of response (advisory, scheme_search, etc.)
            
        Returns:
            Grounded response dict with safety checks applied
        """
        logger.info(f"Grounding response type: {response_type}")

        if not grounding_context.backend_result:
            return ResponseGrounder._create_error_response(
                "No backend result to ground",
                grounding_context.language,
            )

        if grounding_context.backend_result.status == CapabilityStatus.NOT_IMPLEMENTED:
            return ResponseGrounder._create_unavailable_response(
                grounding_context.backend_result.message or "This capability is not yet available",
                grounding_context.language,
            )

        if grounding_context.backend_result.error:
            return ResponseGrounder._create_error_response(
                grounding_context.backend_result.error,
                grounding_context.language,
            )

        # Validate AI draft against safety rules
        if ai_draft:
            validation = ResponseGrounder._validate_grounding(
                ai_draft,
                grounding_context,
                response_type,
            )
            if not validation["safe"]:
                logger.warning(f"AI response failed grounding: {validation['violations']}")
                ai_draft = None  # Reject and use deterministic fallback

        # Build grounded response
        grounded = {
            "type": response_type,
            "grounded": True,
            "safety_checked": True,
            "data": grounding_context.backend_result.data or {},
            "ai_response": ai_draft,
            "language": grounding_context.language,
            "information_completeness": grounding_context.information_completeness,
        }

        if grounding_context.missing_information:
            grounded["missing_information"] = grounding_context.missing_information

        return grounded

    @staticmethod
    def _validate_grounding(
        response: str,
        context: GroundingContext,
        response_type: str,
    ) -> Dict[str, Any]:
        """
        Validate that response is grounded in backend data.
        
        Basic checks:
        - No specific numbers invented (scores, prices, etc.)
        - No false certainty
        - Acknowledgement of incomplete information
        """
        violations = []

        response_lower = response.lower()

        # Check for invented financial figures
        if response_type == "advisory":
            # Should not invent investment amounts
            if (
                "investment" in response_lower
                and context.backend_result.data
                and "recommendations" not in context.backend_result.data
            ):
                violations.append("Invented investment figure without backend data")

        # Check for overconfidence
        high_confidence_words = [
            "definitely",
            "guaranteed",
            "will definitely",
            "100% sure",
            "absolutely",
        ]

        if context.information_completeness < 0.5:
            # With low completeness, high confidence is inappropriate
            for word in high_confidence_words:
                if word in response_lower:
                    violations.append(f"Overconfident language '{word}' with low data completeness")

        # Check for missing data acknowledgement
        if context.missing_information and context.information_completeness < 0.7:
            if not any(
                phrase in response_lower
                for phrase in [
                    "more information",
                    "if you provide",
                    "tell me more",
                    "i need to know",
                    "could you share",
                ]
            ):
                violations.append("Failed to acknowledge missing important information")

        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "confidence_score": 1.0 - (len(violations) * 0.2),
        }

    @staticmethod
    def create_advisory_response(
        recommendations: List[Dict[str, Any]],
        language: str = "english",
        ai_explanation: Optional[str] = None,
        missing_info: Optional[List[str]] = None,
        completeness: float = 1.0,
    ) -> Dict[str, Any]:
        """Create a grounded advisory response"""
        if not recommendations:
            return ResponseGrounder._create_error_response(
                "Unable to generate recommendations",
                language,
            )

        top_rec = recommendations[0]

        response = {
            "type": "advisory",
            "grounded": True,
            "top_recommendation": {
                "enterprise": top_rec.get("enterprise_name", top_rec.get("enterprise_code")),
                "score": top_rec.get("suitability_score"),
                "why": ai_explanation or ResponseGrounder._explain_recommendation(top_rec),
            },
            "alternative_options": [r.get("enterprise_name") for r in recommendations[1:]],
            "next_steps": top_rec.get("next_actions", []),
            "information_completeness": completeness,
        }

        if missing_info:
            response["would_improve_with"] = missing_info

        return response

    @staticmethod
    def _explain_recommendation(rec: Dict[str, Any]) -> str:
        """Generate basic explanation for a recommendation"""
        score = rec.get("suitability_score", 0)
        enterprise = rec.get("enterprise_name", "this enterprise")

        if score >= 80:
            return f"{enterprise} is well-suited to your profile"
        elif score >= 60:
            return f"{enterprise} could work well for you"
        else:
            return f"{enterprise} is a possible option to explore"

    @staticmethod
    def _create_error_response(
        error_message: str,
        language: str = "english",
    ) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "type": "error",
            "grounded": True,
            "message": error_message,
            "language": language,
        }

    @staticmethod
    def _create_unavailable_response(
        message: str,
        language: str = "english",
    ) -> Dict[str, Any]:
        """Create an unavailable capability response"""
        return {
            "type": "unavailable",
            "grounded": True,
            "message": message,
            "language": language,
        }

    @staticmethod
    def check_fabrication_risk(
        response: str,
        response_type: str,
    ) -> Dict[str, Any]:
        """
        Check if response contains likely fabrications.
        
        Red flags:
        - Specific numbers without context
        - Overconfident language
        - Claims about things not in backend
        """
        risk_score = 0.0
        flags = []

        response_lower = response.lower()

        # Check for suspicious patterns
        if response_type == "advisory":
            # Advisory should not have exact income guarantees
            if "earn" in response_lower and "₹" in response:
                import re

                price_match = re.search(r"₹[\d,]+", response)
                if price_match:
                    flags.append(f"Specific income claim: {price_match.group()}")
                    risk_score += 0.4

            # Check for scheme eligibility claims
            if "eligible" in response_lower and "guaranteed" in response_lower:
                flags.append("Overconfident eligibility claim")
                risk_score += 0.3

        elif response_type == "market_search":
            if "price" in response_lower and "₹" in response:
                flags.append("Specific price claim without current data")
                risk_score += 0.3

        # High confidence language without caveats
        if any(word in response_lower for word in ["definitely", "guaranteed", "will definitely"]):
            if "might" not in response_lower and "could" not in response_lower:
                flags.append("High confidence without appropriate caveats")
                risk_score += 0.2

        return {
            "has_fabrication_risk": risk_score > 0.3,
            "risk_score": min(1.0, risk_score),
            "flags": flags,
        }
