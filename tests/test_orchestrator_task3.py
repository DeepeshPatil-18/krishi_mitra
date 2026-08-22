"""Tests for TASK 3 - AI Orchestrator and Farmer Assistant"""

import pytest
from app.services.ai_orchestrator import AIOrchestrator, OrchestratorContext, CapabilityStatus
from app.services.entity_extractor import EntityExtractor
from app.services.response_grounder import ResponseGrounder, GroundingContext
from app.services.krishimitra_prompts import KrishiMitraPrompts
from app.schemas.intent import Intent
from app.schemas.advisory import FarmerContext


class TestEntityExtractor:
    """Test entity extraction from farmer messages"""

    def test_extract_budget_english(self):
        """Extract budget from English message"""
        msg = "I have 50000 rupees"
        budget = EntityExtractor.extract_budget(msg)
        assert budget == 50000

    def test_extract_budget_marathi(self):
        """Extract budget from Marathi message with digits"""
        msg = "50 हजार रुपये"
        budget = EntityExtractor.extract_budget(msg)
        assert budget == 50000

    def test_extract_budget_with_thousand_keyword(self):
        """Extract budget with 'thousand' keyword"""
        msg = "50 thousand rupees"
        budget = EntityExtractor.extract_budget(msg)
        assert budget == 50000

    def test_extract_location_maharashtra(self):
        """Extract location - Maharashtra"""
        msg = "I am in Maharashtra"
        location = EntityExtractor.extract_location(msg)
        assert location == "maharashtra"

    def test_extract_location_marathi(self):
        """Extract location from Marathi text"""
        msg = "मी महाराष्ट्रमध्ये आहे"
        location = EntityExtractor.extract_location(msg)
        assert location == "maharashtra"

    def test_extract_land_hectares(self):
        """Extract land size in hectares"""
        msg = "I have 2 hectares of land"
        land = EntityExtractor.extract_land(msg)
        assert land == 2.0

    def test_extract_land_small(self):
        """Extract small land size"""
        msg = "0.1 ha available"
        land = EntityExtractor.extract_land(msg)
        assert land == 0.1

    def test_extract_all_entities(self):
        """Extract all entities from complex message"""
        msg = "I'm in Maharashtra with ₹50000, 2 hectares, beginner at farming, medium water availability"
        entities = EntityExtractor.extract_all(msg)
        
        assert entities.get("budget_rupees") == 50000
        assert entities.get("land_size_hectares") == 2.0
        assert entities.get("location") == "maharashtra"
        assert entities.get("experience_level") == "beginner"
        assert entities.get("water_availability") == "medium"

    def test_extract_enterprise_mushroom(self):
        """Extract enterprise - mushroom"""
        msg = "I want to start mushroom cultivation"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("enterprise") == "mushroom"

    def test_extract_enterprise_marathi(self):
        """Extract enterprise from Marathi"""
        msg = "मी मशरूम शेती सुरू करू इच्छितो"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("enterprise") == "mushroom"

    def test_extract_risk_tolerance(self):
        """Extract risk tolerance"""
        msg = "I prefer low risk, safe investments"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("risk_tolerance") == "low"

    def test_extract_time_availability(self):
        """Extract time availability"""
        msg = "I can work full time on this"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("time_availability") == "full_time"

    def test_extract_no_entities(self):
        """Handle message with no extractable entities"""
        msg = "Hello, how are you?"
        entities = EntityExtractor.extract_all(msg)
        assert len(entities) == 0 or all(v is None for v in entities.values())


class TestOrchestratorContext:
    """Test orchestrator context building"""

    def test_orchestrate_english_livelihood(self):
        """Orchestrate English livelihood recommendation request"""
        msg = "I have 50000 rupees in Maharashtra. What should I start?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx.detected_language == "english"
        assert ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION
        assert ctx.intent_confidence > 0.7
        assert ctx.farmer_context is not None
        assert ctx.farmer_context.budget_rupees == 50000
        assert ctx.farmer_context.location == "maharashtra"

    def test_orchestrate_marathi_livelihood(self):
        """Orchestrate Marathi livelihood request"""
        msg = "50 हजार रुपये आहेत. मी काय सुरू करू?"
        ctx = AIOrchestrator.orchestrate(msg, language="marathi")
        
        assert ctx.detected_language == "marathi"
        assert ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION
        assert ctx.farmer_context.budget_rupees == 50000

    def test_orchestrate_hindi_livelihood(self):
        """Orchestrate Hindi livelihood request"""
        msg = "मेरे पास पचास हजार रुपये हैं। मैं क्या शुरू कर सकता हूँ?"
        ctx = AIOrchestrator.orchestrate(msg, language="hindi")
        
        assert ctx.detected_language == "hindi"
        assert ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION

    def test_orchestrate_scheme_search(self):
        """Orchestrate scheme search intent"""
        msg = "What government schemes are available?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx.intent == Intent.SCHEME_SEARCH

    def test_orchestrate_training_request(self):
        """Orchestrate training request intent"""
        msg = "How do I learn mushroom farming?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx.intent == Intent.TRAINING_REQUEST

    def test_orchestrate_market_search(self):
        """Orchestrate market search intent"""
        msg = "Where can I sell my honey?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx.intent == Intent.MARKET_SEARCH

    def test_orchestrate_with_provided_context(self):
        """Orchestrate with pre-provided farmer context"""
        msg = "What should I do?"
        provided_ctx = {
            "budget_rupees": 100000,
            "land_size_hectares": 1.5,
            "experience_level": "intermediate"
        }
        
        ctx = AIOrchestrator.orchestrate(
            msg,
            language="english",
            provided_context=provided_ctx
        )
        
        assert ctx.farmer_context.budget_rupees == 100000
        assert ctx.farmer_context.land_size_hectares == 1.5
        assert ctx.farmer_context.experience_level == "intermediate"

    def test_orchestrate_missing_information_advisory(self):
        """Identify missing information for advisory"""
        msg = "I have 50000 rupees"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        # Should identify missing: land, experience, location, etc.
        assert len(ctx.missing_information) > 0
        assert ctx.information_completeness < 0.6

    def test_orchestrate_complete_information_advisory(self):
        """Calculate completeness with full information"""
        msg = "I'm in Maharashtra with 50000 rupees, 2 hectares, beginner, medium water"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        # Should have high completeness
        assert ctx.information_completeness > 0.6

    def test_orchestrate_auto_language_detection(self):
        """Auto-detect language when set to 'auto'"""
        msg = "माझ्याकडे ५० हजार रुपये आहेत"
        ctx = AIOrchestrator.orchestrate(msg, language="auto")
        
        assert ctx.detected_language == "marathi"

    def test_orchestrate_language_override(self):
        """Allow explicit language override"""
        msg = "माझ्याकडे ५० हजार रुपये आहेत"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        # Should use provided language
        assert ctx.detected_language == "english"


class TestOrchestratorCapabilityExecution:
    """Test capability execution"""

    def test_execute_advisory_capability(self):
        """Execute advisory capability"""
        ctx = OrchestratorContext(
            intent=Intent.LIVELIHOOD_RECOMMENDATION,
            farmer_context=FarmerContext(
                budget_rupees=50000,
                land_size_hectares=0.1,
                experience_level="beginner"
            )
        )
        
        result = AIOrchestrator.execute_capability(ctx)
        
        assert result.status == CapabilityStatus.AVAILABLE
        assert result.data is not None
        assert "recommendations" in result.data
        assert len(result.data["recommendations"]) > 0

    def test_execute_advisory_with_no_context(self):
        """Execute advisory without farmer context"""
        ctx = OrchestratorContext(intent=Intent.LIVELIHOOD_RECOMMENDATION)
        result = AIOrchestrator.execute_capability(ctx)
        
        assert result.error is not None

    def test_execute_scheme_search_capability(self):
        """Execute scheme search capability"""
        ctx = OrchestratorContext(
            intent=Intent.SCHEME_SEARCH,
            farmer_context=FarmerContext(location="maharashtra")
        )
        
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.AVAILABLE

    def test_execute_training_capability(self):
        """Execute training request capability"""
        ctx = OrchestratorContext(
            intent=Intent.TRAINING_REQUEST,
            extracted_entities={"enterprise": "mushroom"}
        )
        
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.AVAILABLE

    def test_execute_market_search_capability(self):
        """Execute market search capability"""
        ctx = OrchestratorContext(
            intent=Intent.MARKET_SEARCH,
            farmer_context=FarmerContext(location="maharashtra")
        )
        
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.AVAILABLE

    def test_execute_expert_request_capability(self):
        """Execute expert request (not implemented)"""
        ctx = OrchestratorContext(intent=Intent.EXPERT_REQUEST)
        result = AIOrchestrator.execute_capability(ctx)
        
        assert result.status == CapabilityStatus.NOT_IMPLEMENTED
        assert result.message is not None

    def test_execute_community_capability(self):
        """Execute community request (not implemented)"""
        ctx = OrchestratorContext(intent=Intent.COMMUNITY)
        result = AIOrchestrator.execute_capability(ctx)
        
        assert result.status == CapabilityStatus.NOT_IMPLEMENTED
        assert result.message is not None

    def test_execute_general_qa_capability(self):
        """Execute general Q&A capability"""
        ctx = OrchestratorContext(intent=Intent.GENERAL_QUESTION)
        result = AIOrchestrator.execute_capability(ctx)
        
        assert result.status == CapabilityStatus.AVAILABLE
        assert result.data is not None


class TestResponseGrounding:
    """Test response grounding and safety"""

    def test_ground_advisory_response(self):
        """Ground advisory response in backend data"""
        backend_result = {
            "status": "available",
            "data": {
                "recommendations": [{
                    "enterprise_name": "Mushroom",
                    "suitability_score": 82.5
                }]
            }
        }
        
        ctx = GroundingContext(
            backend_result=backend_result,
            language="english",
            information_completeness=0.8
        )
        
        grounded = ResponseGrounder.ground_response(ctx, response_type="advisory")
        assert grounded["grounded"] is True

    def test_fabrication_risk_detection(self):
        """Detect potential fabrication in response"""
        response = "You will definitely earn ₹50,000 per month with guaranteed success"
        
        risk = ResponseGrounder.check_fabrication_risk(response, "advisory")
        assert risk["has_fabrication_risk"] is True
        assert len(risk["flags"]) > 0

    def test_no_fabrication_risk(self):
        """Validate response with no fabrication risk"""
        response = "Based on your situation, Mushroom Cultivation could work well for you. You might earn ₹12,000-20,000 per month depending on management."
        
        risk = ResponseGrounder.check_fabrication_risk(response, "advisory")
        assert risk["has_fabrication_risk"] is False or risk["risk_score"] < 0.3

    def test_grounding_unavailable_capability(self):
        """Handle unavailable capability response"""
        from app.services.ai_orchestrator import CapabilityResult
        
        backend_result = CapabilityResult(
            status=CapabilityStatus.NOT_IMPLEMENTED,
            message="Expert consultation coming soon"
        )
        
        ctx = GroundingContext(backend_result=backend_result, language="english")
        grounded = ResponseGrounder.ground_response(ctx, response_type="expert")
        
        assert grounded["type"] == "unavailable"


class TestKrishiMitraPrompts:
    """Test system prompts for KrishiMitra"""

    def test_get_base_system_prompt(self):
        """Get base system prompt"""
        prompt = KrishiMitraPrompts.get_base_system_prompt()
        
        assert "KrishiMitra" in prompt
        assert "not fabricate" in prompt.lower()

    def test_get_english_prompt(self):
        """Get English language prompt"""
        prompt = KrishiMitraPrompts.get_language_prompt("english")
        
        assert len(prompt) > 0
        assert "simple English" in prompt or "Simple" in prompt

    def test_get_marathi_prompt(self):
        """Get Marathi language prompt"""
        prompt = KrishiMitraPrompts.get_language_prompt("marathi")
        
        assert len(prompt) > 0
        assert "मराठी" in prompt or "मराठ" in prompt

    def test_get_hindi_prompt(self):
        """Get Hindi language prompt"""
        prompt = KrishiMitraPrompts.get_language_prompt("hindi")
        
        assert len(prompt) > 0
        assert "हिंदी" in prompt or "हिन्द" in prompt

    def test_safety_constraints(self):
        """Get safety constraints for response types"""
        advisory_constraints = KrishiMitraPrompts.get_safety_constraints("advisory")
        
        assert "SAFETY CONSTRAINTS" in advisory_constraints
        assert "suitability" in advisory_constraints.lower()


class TestMultilingualResponses:
    """Test multilingual support across the orchestrator"""

    def test_english_response_generation(self):
        """Generate English response"""
        msg = "I have 50000 rupees. What can I start?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx.detected_language == "english"
        assert ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION

    def test_marathi_response_generation(self):
        """Generate Marathi response"""
        msg = "माझ्याकडे ५० हजार रुपये आहेत. मी काय सुरू करू?"
        ctx = AIOrchestrator.orchestrate(msg, language="marathi")
        
        assert ctx.detected_language == "marathi"

    def test_hindi_response_generation(self):
        """Generate Hindi response"""
        msg = "मेरे पास पचास हजार रुपये हैं। मैं क्या शुरू कर सकता हूँ?"
        ctx = AIOrchestrator.orchestrate(msg, language="hindi")
        
        assert ctx.detected_language == "hindi"

    def test_language_auto_detection_marathi(self):
        """Auto-detect Marathi"""
        msg = "50 हजार रुपये आहेत"
        ctx = AIOrchestrator.orchestrate(msg, language="auto")
        
        assert ctx.detected_language == "marathi"

    def test_language_auto_detection_english(self):
        """Auto-detect English"""
        msg = "I have 50000 rupees"
        ctx = AIOrchestrator.orchestrate(msg, language="auto")
        
        assert ctx.detected_language == "english"


class TestIntegration:
    """Integration tests for complete orchestration"""

    def test_full_orchestration_flow(self):
        """Test complete orchestration flow: detect -> execute -> ground"""
        msg = "I have 50000 rupees in Maharashtra with 0.1 hectares. I'm a beginner. What should I start?"
        
        # Step 1: Orchestrate
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION
        assert ctx.information_completeness > 0.6
        
        # Step 2: Execute
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.AVAILABLE
        assert result.data is not None
        
        # Step 3: Ground
        grounding_ctx = GroundingContext(
            backend_result=result,
            language=ctx.detected_language,
            information_completeness=ctx.information_completeness
        )
        grounded = ResponseGrounder.ground_response(grounding_ctx, response_type="advisory")
        assert grounded["grounded"] is True

    def test_no_hallucination_fabrication(self):
        """Verify system doesn't fabricate enterprise scores"""
        msg = "I have 100 rupees only"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        # Even with minimal budget, should return real scores from engine
        result = AIOrchestrator.execute_capability(ctx)
        
        if result.status == CapabilityStatus.AVAILABLE and result.data:
            recs = result.data.get("recommendations", [])
            if recs:
                # Scores should be in valid range (0-100)
                for rec in recs:
                    score = rec.get("suitability_score")
                    assert 0 <= score <= 100, f"Invalid score: {score}"

    def test_missing_information_identification(self):
        """Verify system identifies missing information correctly"""
        # Minimal message
        msg = "I have 50000 rupees"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        assert len(ctx.missing_information) > 0
        assert ctx.information_completeness < 0.6
        
        # Complete message
        msg_complete = "I'm in Maharashtra with 50000 rupees, 2 hectares, beginner, medium water availability"
        ctx_complete = AIOrchestrator.orchestrate(msg_complete, language="english")
        
        assert len(ctx_complete.missing_information) <= len(ctx.missing_information)
        assert ctx_complete.information_completeness >= ctx.information_completeness

    def test_deterministic_scoring(self):
        """Verify scoring is deterministic (same input = same output)"""
        msg = "I have 50000 rupees in Maharashtra, 0.1 ha, beginner"
        
        # Run orchestration twice
        ctx1 = AIOrchestrator.orchestrate(msg, language="english")
        result1 = AIOrchestrator.execute_capability(ctx1)
        
        ctx2 = AIOrchestrator.orchestrate(msg, language="english")
        result2 = AIOrchestrator.execute_capability(ctx2)
        
        # Should get identical results
        if result1.data and result2.data:
            recs1 = result1.data.get("recommendations", [])
            recs2 = result2.data.get("recommendations", [])
            
            if recs1 and recs2:
                # Top recommendation should be the same
                assert recs1[0].get("enterprise_code") == recs2[0].get("enterprise_code")
                assert recs1[0].get("suitability_score") == recs2[0].get("suitability_score")
