"""API integration tests"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "version" in data
        assert "documentation" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "environment" in data
    
    def test_docs_endpoint(self):
        """Test OpenAPI docs"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_schema(self):
        """Test OpenAPI schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestIntentDetection:
    """Test intent detection endpoint"""
    
    def test_intent_market_search_english(self):
        """Test market search intent in English"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "Where can I sell my honey?",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "market_search"
        assert data["confidence"] > 0.8
        assert data["detected_language"] == "english"
    
    def test_intent_scheme_search_hindi(self):
        """Test scheme search intent in Hindi"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "मला शेळीपालनासाठी सरकारी मदत मिळेल का?",
                "language": "marathi"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "scheme_search"
        assert data["confidence"] > 0.8
    
    def test_intent_training_request_marathi(self):
        """Test training request intent in Marathi"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "मशरूम शेती कशी सुरू करू?",
                "language": "marathi"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "training_request"
        assert data["confidence"] > 0.8
    
    def test_intent_expert_request(self):
        """Test expert request intent"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "I need to speak with an expert",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "expert_request"
    
    def test_intent_livelihood_recommendation(self):
        """Test livelihood recommendation intent"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "माझ्याकडे ५० हजार आहेत. मी काय सुरू करू?",
                "language": "marathi"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "livelihood_recommendation"
    
    def test_intent_empty_message(self):
        """Test error handling for empty message"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "",
                "language": "english"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_intent_invalid_language(self):
        """Test error handling for invalid language"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "Hello",
                "language": "invalid_lang"
            }
        )
        # Should handle gracefully by defaulting to English
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
    
    def test_intent_auto_language_detection(self):
        """Test automatic language detection"""
        response = client.post(
            "/api/v1/intent/detect",
            json={
                "message": "मशरूम शेती",
                "language": "auto"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detected_language"] in ["marathi", "hindi", "english"]


class TestAdvisoryRecommendation:
    """Test advisory recommendation endpoint"""
    
    def test_advisory_basic_recommendation(self):
        """Test basic advisory recommendation"""
        response = client.post(
            "/api/v1/advisory/recommend",
            json={
                "budget_rupees": 50000,
                "land_size_hectares": 2.0,
                "state": "maharashtra",
                "experience_level": "beginner"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["farmer_budget"] == 50000
        assert data["farmer_land"] == 2.0
        assert len(data["recommendations"]) > 0
        
        # Check recommendation structure
        rec = data["recommendations"][0]
        assert "enterprise_code" in rec
        assert "enterprise_name" in rec
        assert "suitability_score" in rec
        assert "reasons" in rec
        assert "estimated_investment" in rec
        assert "requirements" in rec
        assert "risks" in rec
    
    def test_advisory_low_budget(self):
        """Test recommendation with low budget"""
        response = client.post(
            "/api/v1/advisory/recommend",
            json={
                "budget_rupees": 15000,
                "land_size_hectares": 0.1,
                "state": "maharashtra"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) > 0
        # Lower budget enterprises should be recommended
        assert data["recommendations"][0]["estimated_investment"] <= 50000
    
    def test_advisory_large_land(self):
        """Test recommendation with large land"""
        response = client.post(
            "/api/v1/advisory/recommend",
            json={
                "budget_rupees": 200000,
                "land_size_hectares": 5.0,
                "state": "maharashtra"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) > 0
    
    def test_advisory_invalid_budget(self):
        """Test error handling for invalid budget"""
        response = client.post(
            "/api/v1/advisory/recommend",
            json={
                "budget_rupees": -1000,
                "land_size_hectares": 1.0
            }
        )
        assert response.status_code == 400
    
    def test_advisory_invalid_land(self):
        """Test error handling for negative land"""
        response = client.post(
            "/api/v1/advisory/recommend",
            json={
                "budget_rupees": 50000,
                "land_size_hectares": -1.0
            }
        )
        assert response.status_code == 400
    
    def test_enterprise_details(self):
        """Test enterprise details endpoint"""
        response = client.get("/api/v1/advisory/enterprises/apiculture")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        enterprise = data["data"]
        assert enterprise["code"] == "apiculture"
        assert "name_en" in enterprise
        assert "min_budget_rupees" in enterprise
    
    def test_enterprise_details_not_found(self):
        """Test enterprise details for non-existent enterprise"""
        response = client.get("/api/v1/advisory/enterprises/invalid_enterprise")
        assert response.status_code == 404
    
    def test_schemes_endpoint(self):
        """Test schemes endpoint"""
        response = client.get("/api/v1/advisory/schemes/apiculture?state=maharashtra")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "schemes" in data
        assert len(data["schemes"]) >= 0


class TestAssistantChat:
    """Test assistant chat endpoint"""
    
    def test_assistant_livelihood_recommendation(self):
        """Test assistant livelihood recommendation"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "I have 50000 rupees. What business can I start?",
                "language": "english",
                "farmer_context": {
                    "budget": 50000,
                    "land": 2.0,
                    "experience": "beginner"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "livelihood_recommendation"
        assert "response" in data
        assert len(data["response"]) > 0
        assert data["response_type"] == "advisory"
    
    def test_assistant_marathi_livelihood(self):
        """Test assistant with Marathi livelihood request"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "माझ्याकडे पन्नास हजार रुपये आहेत. मी काय सुरू करू?",
                "language": "marathi"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "livelihood_recommendation"
        assert "response" in data
    
    def test_assistant_scheme_search(self):
        """Test assistant scheme search"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "What government schemes are available for beekeeping?",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "scheme_search"
        assert "response" in data
    
    def test_assistant_training_request(self):
        """Test assistant training request"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "How do I start mushroom cultivation?",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "training_request"
        assert "response" in data
    
    def test_assistant_market_search(self):
        """Test assistant market search"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "Where can I sell my honey?",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "market_search"
        assert "response" in data
    
    def test_assistant_expert_request(self):
        """Test assistant expert request"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "I need expert guidance on goat farming",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "expert_request"
        assert "response" in data
    
    def test_assistant_empty_message(self):
        """Test error handling for empty message"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "",
                "language": "english"
            }
        )
        assert response.status_code == 400
    
    def test_assistant_auto_language_detection(self):
        """Test assistant with auto language detection"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "मशरूम शेतीचे फायदे काय आहेत?",
                "language": "auto"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_assistant_response_format(self):
        """Test assistant response format"""
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "I want to start a business",
                "language": "english"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "intent" in data
        assert "response" in data
        assert "response_type" in data
        assert "requires_further_input" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0


class TestExistingUnitTests:
    """Verify existing unit tests still work"""
    
    def test_advisory_engine_integration(self):
        """Test that advisory engine still works"""
        from app.services.advisory_engine import AdvisoryEngine
        
        recommendations = AdvisoryEngine.recommend_enterprises(
            budget_rupees=50000,
            land_size_hectares=2.0,
            state="maharashtra",
            experience_level="beginner"
        )
        
        assert len(recommendations) > 0
        assert all(0 <= rec.suitability_score <= 100 for rec in recommendations)
    
    def test_intent_router_integration(self):
        """Test that intent router still works"""
        from app.services.intent_router import IntentRouter
        from app.schemas.intent import Intent
        
        intent, confidence, params = IntentRouter.detect_intent(
            "माझा मध कुठे विकू?"
        )
        
        assert intent == Intent.MARKET_SEARCH
        assert confidence > 0.8


class TestDataProviders:
    """Test data provider functionality"""
    
    def test_enterprise_provider(self):
        """Test enterprise provider"""
        from app.services.data_provider import EnterpriseProvider
        
        enterprises = EnterpriseProvider.get_all_enterprises()
        assert len(enterprises) > 0
        
        ent = EnterpriseProvider.get_enterprise_by_code("apiculture")
        assert ent is not None
        assert ent["code"] == "apiculture"
    
    def test_scheme_provider(self):
        """Test scheme provider"""
        from app.services.data_provider import SchemeProvider
        
        schemes = SchemeProvider.get_all_schemes()
        assert len(schemes) > 0
        
        schemes_by_ent = SchemeProvider.get_schemes_by_enterprise("apiculture")
        assert len(schemes_by_ent) >= 0
    
    def test_training_provider(self):
        """Test training provider"""
        from app.services.data_provider import TrainingProvider
        
        modules = TrainingProvider.get_all_training_modules()
        assert len(modules) > 0
    
    def test_market_provider(self):
        """Test market provider"""
        from app.services.data_provider import MarketProvider
        
        markets = MarketProvider.get_all_markets()
        assert len(markets) > 0
    
    def test_expert_provider(self):
        """Test expert provider"""
        from app.services.data_provider import ExpertProvider
        
        experts = ExpertProvider.get_all_experts()
        assert len(experts) > 0
