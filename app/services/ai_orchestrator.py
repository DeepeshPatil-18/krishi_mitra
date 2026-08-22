"""AI Orchestrator - central coordination for farmer requests"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.schemas.intent import Intent
from app.services.language_service import LanguageService
from app.services.intent_router import IntentRouter
from app.services.advisory_engine_v2 import AdvisoryEngineV2
from app.services.data_provider import (
    SchemeProvider,
    TrainingProvider,
    MarketProvider,
)
from app.services.scheme_service import SchemeService
from app.services.market_service import MarketService
from app.schemas.advisory import FarmerContext

logger = logging.getLogger(__name__)


class CapabilityStatus(str, Enum):
    """Capability implementation status"""
    AVAILABLE = "available"
    NOT_IMPLEMENTED = "not_implemented"
    REQUIRES_UPGRADE = "requires_upgrade"


@dataclass
class CapabilityResult:
    """Result from executing a capability"""
    status: CapabilityStatus
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


@dataclass
class OrchestratorContext:
    """Lightweight context for current request"""
    farmer_id: Optional[str] = None
    message: str = ""
    language: str = "english"
    detected_language: str = "english"
    intent: Optional[Intent] = None
    intent_confidence: float = 0.0
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    farmer_context: Optional[FarmerContext] = None
    missing_information: List[str] = field(default_factory=list)
    information_completeness: float = 0.0


class AIOrchestrator:
    """
    Central coordinator for farmer requests.
    
    Orchestrates:
    1. Language detection
    2. Intent detection
    3. Entity extraction
    4. Capability selection
    5. Service calls
    6. Response generation
    """

    # Intent to capability mapping
    INTENT_CAPABILITY_MAP = {
        Intent.LIVELIHOOD_RECOMMENDATION: "advisory",
        Intent.SCHEME_SEARCH: "scheme_search",
        Intent.TRAINING_REQUEST: "training_request",
        Intent.MARKET_SEARCH: "market_search",
        Intent.EXPERT_REQUEST: "expert_request",
        Intent.GENERAL_QUESTION: "general_qa",
        Intent.COMMUNITY: "community",
    }

    @staticmethod
    def orchestrate(
        message: str,
        language: Optional[str] = None,
        farmer_id: Optional[str] = None,
        provided_context: Optional[Dict[str, Any]] = None,
    ) -> OrchestratorContext:
        """
        Main orchestration method.
        
        Flow:
        1. Validate input
        2. Detect language
        3. Build initial context
        4. Detect intent
        5. Extract entities
        6. Build farmer context
        7. Return orchestrator context
        
        Args:
            message: Farmer's message
            language: Optional language override
            farmer_id: Optional farmer identifier
            provided_context: Optional context dict (budget, land, etc.)
            
        Returns:
            OrchestratorContext with detected info
        """
        logger.info(f"Orchestrating message: {message[:50]}...")
        
        # Create empty context
        ctx = OrchestratorContext(
            farmer_id=farmer_id,
            message=message,
            language=language or "auto",
        )

        try:
            # Step 1: Detect language
            if ctx.language == "auto" or not LanguageService.validate_language(ctx.language):
                ctx.detected_language = LanguageService.detect_language(message)
            else:
                ctx.detected_language = ctx.language.lower()

            # Step 2: Detect intent
            intent, confidence, base_params = IntentRouter.detect_intent(
                message=message,
                language=ctx.detected_language,
                context=provided_context or {},
            )

            ctx.intent = intent
            ctx.intent_confidence = confidence

            # Step 3: Extract entities WITH NORMALIZATION
            from app.services.entity_extractor import EntityExtractor
            from app.services.entity_normalizer import EntityNormalizer
            
            # 3a. Extract raw entities using EntityExtractor
            raw_entities = EntityExtractor.extract_all(
                message=message,
                language=ctx.detected_language
            )
            
            # 3b. Normalize each entity using EntityNormalizer
            # Note: EntityExtractor already normalizes numeric fields (budget, land)
            # EntityNormalizer handles additional complex cases (fractions, ranges, approximations)
            normalized_entities = {}
            for entity_type, raw_value in raw_entities.items():
                if raw_value is not None:
                    # If value is already numeric (int/float), use it directly
                    if isinstance(raw_value, (int, float)):
                        normalized_entities[entity_type] = raw_value
                    else:
                        # If value is string, try normalization
                        norm_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
                        normalized_value = norm_result.get('normalized_value')
                        
                        if normalized_value is not None:
                            normalized_entities[entity_type] = normalized_value
                        # If normalization fails, don't store entity (avoid bad data)
            
            # 3c. Merge with base_params from intent detection (base_params takes priority)
            normalized_entities.update(base_params)
            
            # 3d. Store normalized entities
            ctx.extracted_entities = normalized_entities

            # Step 4: Build farmer context from provided + normalized entities
            ctx.farmer_context = AIOrchestrator._build_farmer_context(
                provided_context or {},
                normalized_entities,
                ctx.detected_language,
            )

            # Step 5: Identify missing information
            ctx.missing_information = AIOrchestrator._identify_missing_information(
                ctx.farmer_context,
                ctx.intent,
            )

            # Step 6: Calculate information completeness
            ctx.information_completeness = AIOrchestrator._calculate_completeness(
                ctx.farmer_context,
                ctx.intent,
            )

            logger.info(
                f"Orchestration complete: intent={ctx.intent.value}, "
                f"confidence={ctx.intent_confidence:.2f}, "
                f"completeness={ctx.information_completeness:.2f}"
            )

            return ctx

        except Exception as e:
            logger.error(f"Orchestration error: {e}", exc_info=True)
            raise

    @staticmethod
    def execute_capability(
        ctx: OrchestratorContext,
    ) -> CapabilityResult:
        """
        Execute the capability for detected intent.
        
        Args:
            ctx: Orchestrator context from orchestrate()
            
        Returns:
            CapabilityResult with data or error
        """
        if not ctx.intent:
            return CapabilityResult(
                status=CapabilityStatus.NOT_IMPLEMENTED,
                error="No intent detected",
            )

        capability = AIOrchestrator.INTENT_CAPABILITY_MAP.get(ctx.intent)

        if not capability:
            return CapabilityResult(
                status=CapabilityStatus.NOT_IMPLEMENTED,
                error=f"Unknown intent: {ctx.intent.value}",
            )

        logger.info(f"Executing capability: {capability}")

        try:
            if capability == "advisory":
                return AIOrchestrator._execute_advisory(ctx)
            elif capability == "scheme_search":
                return AIOrchestrator._execute_scheme_search(ctx)
            elif capability == "training_request":
                return AIOrchestrator._execute_training_request(ctx)
            elif capability == "market_search":
                return AIOrchestrator._execute_market_search(ctx)
            elif capability == "expert_request":
                return AIOrchestrator._execute_expert_request(ctx)
            elif capability == "general_qa":
                return AIOrchestrator._execute_general_qa(ctx)
            elif capability == "community":
                return AIOrchestrator._execute_community(ctx)
            else:
                return CapabilityResult(
                    status=CapabilityStatus.NOT_IMPLEMENTED,
                    error=f"Capability not implemented: {capability}",
                )

        except Exception as e:
            logger.error(f"Capability execution error: {e}", exc_info=True)
            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                error=str(e),
            )

    @staticmethod
    def _execute_advisory(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute livelihood advisory capability"""
        try:
            if not ctx.farmer_context:
                return CapabilityResult(
                    status=CapabilityStatus.AVAILABLE,
                    error="No farmer context to evaluate",
                )

            recommendations = AdvisoryEngineV2.evaluate_farmer(ctx.farmer_context)

            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                data={
                    "recommendations": [r.dict() for r in recommendations],
                    "count": len(recommendations),
                    "information_completeness": ctx.information_completeness,
                    "missing_information": ctx.missing_information,
                },
            )

        except Exception as e:
            logger.error(f"Advisory execution error: {e}", exc_info=True)
            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                error=f"Advisory failed: {str(e)}",
            )

    @staticmethod
    def _execute_scheme_search(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute scheme search capability using verified scheme dataset"""
        location = ctx.farmer_context.location if ctx.farmer_context else "maharashtra"
        enterprise = ctx.extracted_entities.get("enterprise")

        try:
            # Use the new SchemeService with deterministic search and ranking
            search_results = SchemeService.search_schemes(
                query=ctx.message,
                location=location,
                enterprise=enterprise,
                extracted_entities=ctx.extracted_entities,
                limit=5
            )

            # Format results for farmer
            formatted_response = SchemeService.format_results(
                results=search_results,
                language=ctx.detected_language
            )

            # Extract scheme data for API response
            schemes_data = [
                {
                    "id": result.scheme.get("id"),
                    "name": result.scheme.get("name"),
                    "summary": result.scheme.get("summary"),
                    "category": result.scheme.get("category"),
                    "source_url": result.scheme.get("source_url"),
                    "source_name": result.scheme.get("source_name"),
                    "relevance_score": result.relevance_score,
                }
                for result in search_results
            ]

            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                data={
                    "schemes": schemes_data,
                    "count": len(schemes_data),
                    "location": location,
                    "enterprise": enterprise,
                    "formatted_response": formatted_response,
                },
                message=formatted_response,
            )

        except Exception as e:
            logger.error(f"Scheme search error: {e}", exc_info=True)
            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                error=f"Scheme search failed: {str(e)}",
            )

    @staticmethod
    def _execute_training_request(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute training request capability"""
        enterprise = ctx.extracted_entities.get("enterprise")

        try:
            if enterprise:
                training = TrainingProvider.get_training_by_enterprise(enterprise)
            else:
                training = TrainingProvider.get_all_training()

            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                data={
                    "training_modules": training,
                    "count": len(training),
                },
            )

        except Exception as e:
            logger.error(f"Training request error: {e}", exc_info=True)
            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                error=f"Training request failed: {str(e)}",
            )

    @staticmethod
    def _execute_market_search(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute market price search capability using official AGMARKNET data"""
        commodity = ctx.extracted_entities.get("commodity") or ctx.extracted_entities.get("product")
        location = ctx.farmer_context.location if ctx.farmer_context else "maharashtra"

        try:
            # Normalize commodity name
            if not commodity:
                return CapabilityResult(
                    status=CapabilityStatus.AVAILABLE,
                    data={
                        "prices": [],
                        "count": 0,
                        "commodity": None,
                        "location": location,
                        "formatted_response": "Please specify a commodity (e.g., onion, tomato, wheat).",
                    },
                )

            # Search for commodity prices
            search_results = MarketService.search_prices(
                commodity=commodity,
                location=location,
                limit=5
            )

            # Format results for farmer
            formatted_response = MarketService.format_results(
                results=search_results,
                language=ctx.detected_language
            )

            # Extract price data for API response
            prices_data = [
                {
                    "commodity": result.commodity,
                    "market": result.market,
                    "location": result.location,
                    "date": result.date,
                    "min_price": result.min_price,
                    "max_price": result.max_price,
                    "modal_price": result.modal_price,
                    "unit": result.unit,
                    "source": result.source,
                    "source_name": result.source_name,
                }
                for result in search_results
            ]

            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                data={
                    "prices": prices_data,
                    "count": len(prices_data),
                    "commodity": commodity,
                    "location": location,
                    "data_source": search_results[0].source if search_results else "UNKNOWN",
                    "formatted_response": formatted_response,
                },
                message=formatted_response,
            )

        except Exception as e:
            logger.error(f"Market search error: {e}", exc_info=True)
            return CapabilityResult(
                status=CapabilityStatus.AVAILABLE,
                error=f"Market search failed: {str(e)}",
            )

    @staticmethod
    def _execute_expert_request(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute expert request capability (not yet implemented)"""
        return CapabilityResult(
            status=CapabilityStatus.NOT_IMPLEMENTED,
            message="Expert consultation is being set up. "
                    "Please contact your local agricultural extension office "
                    "for immediate assistance.",
        )

    @staticmethod
    def _execute_general_qa(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute general Q&A capability (requires AI service)"""
        return CapabilityResult(
            status=CapabilityStatus.AVAILABLE,
            data={
                "requires_ai": True,
                "message": ctx.message,
                "language": ctx.detected_language,
            },
        )

    @staticmethod
    def _execute_community(ctx: OrchestratorContext) -> CapabilityResult:
        """Execute community feature (not yet implemented)"""
        return CapabilityResult(
            status=CapabilityStatus.NOT_IMPLEMENTED,
            message="Community features will be available soon. "
                    "For now, please reach out to your local farming groups.",
        )

    @staticmethod
    def _build_farmer_context(
        provided: Dict[str, Any],
        extracted: Dict[str, Any],
        language: str,
    ) -> Optional[FarmerContext]:
        """
        Build farmer context from provided and extracted data.
        
        Merges provided_context with extracted entities.
        Provided context takes precedence.
        
        Returns None if insufficient data for validation.
        """
        # Merge extracted into provided (provided takes priority)
        merged = {**extracted, **provided}

        # FarmerContext requires at least budget_rupees > 0
        budget = merged.get("budget_rupees") or merged.get("budget")
        if not budget or budget <= 0:
            return None

        try:
            return FarmerContext(
                budget_rupees=budget,
                land_size_hectares=merged.get("land_size_hectares") or merged.get("land"),
                water_availability=merged.get("water_availability"),
                experience_level=merged.get("experience_level") or "beginner",
                location=merged.get("location"),
                income_goal_monthly=merged.get("income_goal_monthly") or merged.get("income_goal"),
                time_availability=merged.get("time_availability"),
                risk_tolerance=merged.get("risk_tolerance"),
                existing_resources=merged.get("existing_resources"),
            )
        except Exception:
            # If validation fails, return None
            return None

    @staticmethod
    def _identify_missing_information(
        farmer_context: Optional[FarmerContext],
        intent: Intent,
    ) -> List[str]:
        """
        Identify missing information that would improve recommendations.
        
        Different intents require different information.
        """
        if not farmer_context:
            return [
                "budget",
                "land_size",
                "water_availability",
                "experience",
                "location",
            ]

        missing = []

        if intent == Intent.LIVELIHOOD_RECOMMENDATION:
            if not farmer_context.budget_rupees:
                missing.append("budget")
            if not farmer_context.land_size_hectares:
                missing.append("land_size")
            if not farmer_context.water_availability:
                missing.append("water_availability")
            if not farmer_context.experience_level:
                missing.append("experience")
            if not farmer_context.location:
                missing.append("location")
            if not farmer_context.income_goal_monthly:
                missing.append("income_goal")
            if not farmer_context.time_availability:
                missing.append("time_availability")

        elif intent == Intent.SCHEME_SEARCH:
            if not farmer_context.location:
                missing.append("location")
            if not farmer_context.experience_level:
                missing.append("experience")

        elif intent == Intent.TRAINING_REQUEST:
            pass  # Can work without context

        elif intent == Intent.MARKET_SEARCH:
            if not farmer_context.location:
                missing.append("location")

        return missing

    @staticmethod
    def _calculate_completeness(
        farmer_context: Optional[FarmerContext],
        intent: Intent,
    ) -> float:
        """
        Calculate information completeness (0.0 to 1.0).
        
        Different intents weight fields differently.
        """
        if not farmer_context:
            return 0.0

        if intent == Intent.LIVELIHOOD_RECOMMENDATION:
            # For advisory, these fields matter most
            key_fields = [
                farmer_context.budget_rupees,
                farmer_context.land_size_hectares,
                farmer_context.experience_level,
                farmer_context.location,
                farmer_context.water_availability,
            ]
            optional_fields = [
                farmer_context.income_goal_monthly,
                farmer_context.time_availability,
                farmer_context.risk_tolerance,
            ]

            key_provided = sum(1 for f in key_fields if f is not None)
            optional_provided = sum(1 for f in optional_fields if f is not None)

            # Base 30% for any attempt + 50% for key fields + 20% for optional
            key_ratio = key_provided / len(key_fields) if key_fields else 0.0
            optional_ratio = (
                optional_provided / len(optional_fields) if optional_fields else 0.0
            )

            return min(1.0, 0.3 + (key_ratio * 0.5) + (optional_ratio * 0.2))

        elif intent == Intent.SCHEME_SEARCH:
            key_fields = [
                farmer_context.location,
            ]
            key_provided = sum(1 for f in key_fields if f is not None)
            return min(1.0, 0.3 + (key_provided / len(key_fields)) * 0.7)

        elif intent == Intent.TRAINING_REQUEST:
            return 0.8  # Training works without much context

        elif intent == Intent.MARKET_SEARCH:
            key_fields = [
                farmer_context.location,
            ]
            key_provided = sum(1 for f in key_fields if f is not None)
            return min(1.0, 0.3 + (key_provided / len(key_fields)) * 0.7)

        else:
            # General questions don't require much context
            return 0.7

    @staticmethod
    def get_capability_status(intent: Intent) -> CapabilityStatus:
        """Check if a capability is implemented"""
        if intent in [
            Intent.LIVELIHOOD_RECOMMENDATION,
            Intent.SCHEME_SEARCH,
            Intent.TRAINING_REQUEST,
            Intent.MARKET_SEARCH,
            Intent.GENERAL_QUESTION,
        ]:
            return CapabilityStatus.AVAILABLE

        return CapabilityStatus.NOT_IMPLEMENTED
