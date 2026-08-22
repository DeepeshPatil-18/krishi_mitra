"""
Integration tests for EntityExtractor + EntityNormalizer in AIOrchestrator pipeline

Tests that entities flow through the complete pipeline:
  Farmer Message → AIOrchestrator → EntityExtractor → EntityNormalizer → FarmerContext
"""

import pytest
from app.services.ai_orchestrator import AIOrchestrator
from app.schemas.intent import Intent


class TestEntityPipelineIntegration:
    """Test complete entity pipeline integration"""
    
    def test_english_budget(self):
        """Test English budget extraction and normalization"""
        message = "I have 50000 rupees budget"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
        assert isinstance(ctx.extracted_entities["budget_rupees"], int)
    
    def test_hindi_budget(self):
        """Test Hindi budget extraction and normalization"""
        message = "मेरे पास 50 हजार रुपये हैं"
        ctx = AIOrchestrator.orchestrate(message, language="hindi")
        
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
        assert isinstance(ctx.extracted_entities["budget_rupees"], int)
    
    def test_marathi_budget(self):
        """Test Marathi budget extraction and normalization"""
        message = "माझ्याकडे 50 हजार रुपये आहेत"
        ctx = AIOrchestrator.orchestrate(message, language="marathi")
        
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
        assert isinstance(ctx.extracted_entities["budget_rupees"], int)
    
    def test_english_land(self):
        """Test English land size extraction and normalization"""
        message = "I have 2 acres of land"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        assert "land_size_hectares" in ctx.extracted_entities
        # 2 acres ≈ 0.809 hectares
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.809) < 0.01
        assert isinstance(ctx.extracted_entities["land_size_hectares"], float)
    
    def test_hindi_land(self):
        """Test Hindi land size extraction and normalization"""
        message = "मेरे पास 2 एकर जमीन है"
        ctx = AIOrchestrator.orchestrate(message, language="hindi")
        
        assert "land_size_hectares" in ctx.extracted_entities
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.809) < 0.01
        assert isinstance(ctx.extracted_entities["land_size_hectares"], float)
    
    def test_marathi_land(self):
        """Test Marathi land size extraction and normalization"""
        message = "माझ्याकडे 2 एकर जमीन आहे"
        ctx = AIOrchestrator.orchestrate(message, language="marathi")
        
        assert "land_size_hectares" in ctx.extracted_entities
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.809) < 0.01
        assert isinstance(ctx.extracted_entities["land_size_hectares"], float)
    
    def test_mixed_language_query(self):
        """Test query with mixed Marathi and English"""
        message = "माझ्याकडे 2 एकर जमीन आणि budget 50000 आहे"
        ctx = AIOrchestrator.orchestrate(message, language="marathi")
        
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
        
        assert "land_size_hectares" in ctx.extracted_entities
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.809) < 0.01
    
    def test_multiple_entities_in_query(self):
        """Test query with multiple entities"""
        message = "मैं नया किसान हूं, मेरे पास 2 एकर जमीन और 50000 रुपये budget है"
        ctx = AIOrchestrator.orchestrate(message, language="hindi")
        
        # Check budget
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
        
        # Check land
        assert "land_size_hectares" in ctx.extracted_entities
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.809) < 0.01
        
        # Check experience
        assert "experience_level" in ctx.extracted_entities
        assert ctx.extracted_entities["experience_level"] == "beginner"
    
    def test_ambiguous_entity(self):
        """Test that ambiguous entities are not stored"""
        message = "I need help with farming"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        # Should not have budget or land (not mentioned)
        assert "budget_rupees" not in ctx.extracted_entities
        assert "land_size_hectares" not in ctx.extracted_entities
    
    def test_no_entities(self):
        """Test query without extractable entities"""
        message = "What are government schemes?"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        # Should detect intent correctly
        assert ctx.intent == Intent.SCHEME_SEARCH
        
        # extracted_entities should be dict (possibly empty or with base_params only)
        assert isinstance(ctx.extracted_entities, dict)
    
    def test_farmer_context_receives_normalized_values(self):
        """Test that FarmerContext is built with normalized values"""
        message = "माझ्याकडे 2 एकर जमीन आणि 50000 रुपये budget आहे"
        ctx = AIOrchestrator.orchestrate(message, language="marathi")
        
        # Check extracted entities are normalized
        assert ctx.extracted_entities["budget_rupees"] == 50000
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.809) < 0.01
        
        # Check farmer context was built
        assert ctx.farmer_context is not None
        
        # Check farmer context has normalized values
        assert ctx.farmer_context.budget_rupees == 50000
        assert abs(ctx.farmer_context.land_size_hectares - 0.809) < 0.01
    
    def test_orchestrator_response_still_works(self):
        """Test that orchestrator returns valid OrchestratorContext"""
        message = "I want to start poultry farming with 50000 rupees"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        # Check context structure
        assert ctx.message == message
        assert ctx.detected_language == "english"
        assert ctx.intent is not None
        assert isinstance(ctx.intent_confidence, float)
        assert isinstance(ctx.extracted_entities, dict)
        assert isinstance(ctx.information_completeness, float)


class TestTask43Improvements:
    """Test TASK 4.3 improvements are active in production"""
    
    def test_land_fraction_marathi(self):
        """Test Marathi fraction support: आधा एकर"""
        message = "माझ्याकडे आधा एकर जमीन आहे"
        ctx = AIOrchestrator.orchestrate(message, language="marathi")
        
        assert "land_size_hectares" in ctx.extracted_entities
        # आधा एकर (0.5 acres) ≈ 0.202 hectares
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.202) < 0.01
    
    def test_land_fraction_hindi(self):
        """Test Hindi fraction support: डेढ़ एकर"""
        message = "मेरे पास डेढ़ एकर जमीन है"
        ctx = AIOrchestrator.orchestrate(message, language="hindi")
        
        assert "land_size_hectares" in ctx.extracted_entities
        # डेढ़ एकर (1.5 acres) ≈ 0.607 hectares
        assert abs(ctx.extracted_entities["land_size_hectares"] - 0.607) < 0.01
    
    def test_budget_range(self):
        """Test budget range support: 50-100k"""
        message = "I have 50-100k budget"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        assert "budget_rupees" in ctx.extracted_entities
        # Range midpoint: (50000 + 100000) / 2 = 75000
        assert ctx.extracted_entities["budget_rupees"] == 75000
    
    def test_budget_approximation_hindi(self):
        """Test budget approximation: लगभग 50000"""
        message = "मेरे पास लगभग 50000 रुपये हैं"
        ctx = AIOrchestrator.orchestrate(message, language="hindi")
        
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
    
    def test_budget_approximation_english(self):
        """Test budget approximation: around 50000"""
        message = "I have around 50000 rupees"
        ctx = AIOrchestrator.orchestrate(message, language="english")
        
        assert "budget_rupees" in ctx.extracted_entities
        assert ctx.extracted_entities["budget_rupees"] == 50000
    
    def test_experience_years_threshold(self):
        """Test experience level year thresholds"""
        # <2 years = beginner
        message_1 = "I have 1 year experience"
        ctx_1 = AIOrchestrator.orchestrate(message_1, language="english")
        assert ctx_1.extracted_entities.get("experience_level") == "beginner"
        
        # 2-10 years = intermediate
        message_2 = "I have 5 years experience"
        ctx_2 = AIOrchestrator.orchestrate(message_2, language="english")
        assert ctx_2.extracted_entities.get("experience_level") == "intermediate"
        
        # >10 years = expert
        message_3 = "I have 15 years experience"
        ctx_3 = AIOrchestrator.orchestrate(message_3, language="english")
        assert ctx_3.extracted_entities.get("experience_level") == "expert"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
