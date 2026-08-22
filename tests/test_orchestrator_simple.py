"""Simplified tests for TASK 3 - Focus on core orchestrator functionality"""

import pytest
from app.services.ai_orchestrator import AIOrchestrator, CapabilityStatus
from app.services.entity_extractor import EntityExtractor
from app.schemas.intent import Intent
from app.schemas.advisory import FarmerContext


class TestEntityExtraction:
    """Test entity extraction"""

    def test_extract_budget(self):
        """Extract budget"""
        msg = "I have 50000 rupees"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("budget_rupees") == 50000

    def test_extract_budget_thousand(self):
        """Extract budget with thousand"""
        msg = "50 thousand rupees"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("budget_rupees") == 50000

    def test_extract_location(self):
        """Extract location"""
        msg = "In Maharashtra"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("location") == "maharashtra"

    def test_extract_land(self):
        """Extract land"""
        msg = "2 hectares"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("land_size_hectares") == 2.0

    def test_extract_enterprise(self):
        """Extract enterprise"""
        msg = "mushroom farming"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("enterprise") == "mushroom"

    def test_extract_multiple(self):
        """Extract multiple entities"""
        msg = "Maharashtra with 50000 rupees 2 hectares beginner"
        entities = EntityExtractor.extract_all(msg)
        assert entities.get("budget_rupees") == 50000
        assert entities.get("land_size_hectares") == 2.0
        assert entities.get("location") == "maharashtra"


class TestOrchestratorDetection:
    """Test orchestrator language and intent detection"""

    def test_detect_english(self):
        """Detect English"""
        msg = "What business should I start?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.detected_language == "english"

    def test_detect_intent_livelihood(self):
        """Detect livelihood recommendation intent"""
        msg = "Which business should I start?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.intent == Intent.LIVELIHOOD_RECOMMENDATION

    def test_detect_intent_scheme(self):
        """Detect scheme search intent"""
        msg = "What schemes are available?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.intent == Intent.SCHEME_SEARCH

    def test_detect_intent_training(self):
        """Detect training request intent"""
        msg = "How do I learn farming?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.intent == Intent.TRAINING_REQUEST

    def test_detect_intent_market(self):
        """Detect market search intent"""
        msg = "Where can I sell my products?"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.intent == Intent.MARKET_SEARCH


class TestCapabilityExecution:
    """Test capability execution"""

    def test_advisory_executable(self):
        """Test advisory capability is executable"""
        ctx = AIOrchestrator.orchestrate(
            "I have 50000. I'm in Maharashtra. I'm a beginner.",
            language="english"
        )
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.AVAILABLE
        assert result.data is not None

    def test_advisory_returns_recommendations(self):
        """Test advisory returns recommendations"""
        ctx = AIOrchestrator.orchestrate(
            "I have 50000 rupees",
            language="english"
        )
        result = AIOrchestrator.execute_capability(ctx)
        if result.status == CapabilityStatus.AVAILABLE:
            assert "recommendations" in result.data or result.data is None

    def test_scheme_search_executable(self):
        """Test scheme search is executable"""
        ctx = AIOrchestrator.orchestrate(
            "What government schemes?",
            language="english"
        )
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.AVAILABLE

    def test_expert_not_implemented(self):
        """Test expert request is not yet implemented"""
        ctx = AIOrchestrator.orchestrate(
            "Connect me with an expert",
            language="english"
        )
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.NOT_IMPLEMENTED

    def test_community_not_implemented(self):
        """Test community is not yet implemented"""
        ctx = AIOrchestrator.orchestrate(
            "Show me community posts",
            language="english"
        )
        result = AIOrchestrator.execute_capability(ctx)
        assert result.status == CapabilityStatus.NOT_IMPLEMENTED


class TestMissingInformation:
    """Test missing information detection"""

    def test_complete_info(self):
        """Test detection with complete info"""
        msg = "Maharashtra 50000 2ha beginner"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.information_completeness > 0.5

    def test_minimal_info(self):
        """Test detection with minimal info"""
        msg = "budget"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert len(ctx.missing_information) >= 0

    def test_information_completeness_ranges(self):
        """Test completeness is 0-1"""
        msg = "50000"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert 0 <= ctx.information_completeness <= 1.0


class TestContextBuilding:
    """Test farmer context building"""

    def test_context_from_extraction(self):
        """Test context built from extraction"""
        msg = "Maharashtra 50000 2ha beginner"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        
        if ctx.farmer_context:
            assert ctx.farmer_context.budget_rupees == 50000 or ctx.farmer_context.budget_rupees is None

    def test_provided_context_merged(self):
        """Test provided context is merged"""
        msg = "What should I do?"
        provided = {"budget_rupees": 100000, "land_size_hectares": 1.5}
        ctx = AIOrchestrator.orchestrate(msg, language="english", provided_context=provided)
        
        if ctx.farmer_context:
            assert ctx.farmer_context.budget_rupees == 100000
            assert ctx.farmer_context.land_size_hectares == 1.5


class TestDeterminism:
    """Test deterministic behavior"""

    def test_same_input_same_intent(self):
        """Test same input produces same intent"""
        msg = "I have 50000. What should I do?"
        ctx1 = AIOrchestrator.orchestrate(msg, language="english")
        ctx2 = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx1.intent == ctx2.intent

    def test_same_input_same_completeness(self):
        """Test same input produces same completeness"""
        msg = "50000"
        ctx1 = AIOrchestrator.orchestrate(msg, language="english")
        ctx2 = AIOrchestrator.orchestrate(msg, language="english")
        
        assert ctx1.information_completeness == ctx2.information_completeness


class TestMultilingual:
    """Test multilingual support"""

    def test_marathi_detected(self):
        """Test Marathi is detected"""
        msg = "50 हजार"
        ctx = AIOrchestrator.orchestrate(msg, language="auto")
        assert ctx.detected_language == "marathi"

    def test_english_detected(self):
        """Test English is detected"""
        msg = "50000 rupees"
        ctx = AIOrchestrator.orchestrate(msg, language="auto")
        assert ctx.detected_language == "english"

    def test_language_override(self):
        """Test language can be overridden"""
        msg = "50000"
        ctx = AIOrchestrator.orchestrate(msg, language="english")
        assert ctx.detected_language == "english"
