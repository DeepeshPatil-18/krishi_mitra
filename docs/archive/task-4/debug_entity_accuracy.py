#!/usr/bin/env python3
"""Debug why entity accuracy is 0% despite seemingly successful extraction"""

import sys
import json
sys.path.insert(0, '.')

from app.services.entity_extractor import EntityExtractor
from app.services.ai_orchestrator import AIOrchestrator

# Sample queries from evaluation dataset
test_queries = [
    {
        "id": "eval_001",
        "message": "माझ्याकडे पन्नास हजार रुपये आहेत. मी काय सुरू करू?",
        "expected_entities": {"budget_rupees": 50000}
    },
    {
        "id": "eval_002",
        "message": "50 हजार आहेत आणि 2 एकर जमीन. मी काय सुरू करू?",
        "expected_entities": {"budget_rupees": 50000, "land_size_hectares": 0.81}
    },
    {
        "id": "eval_003",
        "message": "नाशिकमध्ये 1 एकर जमीन आहे. मशरूम शेती चांगली आहे का?",
        "expected_entities": {"location": "nashik", "land_size_hectares": 0.4047, "enterprise": "mushroom"}
    },
    {
        "id": "eval_004",
        "message": "माझ्याकडे पाणी कमी आहे. कोणता व्यवसाय चांगला होईल?",
        "expected_entities": {"water_availability": "low"}
    }
]

print("="*80)
print("ENTITY EXTRACTION DEBUG - Tracing Full Pipeline")
print("="*80)

for i, query in enumerate(test_queries):
    print(f"\n{'='*80}")
    print(f"Query {i+1}: {query['id']}")
    print(f"Message: {query['message']}")
    print(f"Expected: {json.dumps(query['expected_entities'], indent=2)}")
    
    # Step 1: Extract entities using EntityExtractor
    print("\nSTEP 1: EntityExtractor.extract_all()")
    extracted = EntityExtractor.extract_all(query['message'], language='marathi')
    print(f"Extracted: {json.dumps(extracted, indent=2)}")
    
    # Step 2: Show comparison
    print("\nSTEP 2: Comparison")
    for entity_type, expected_value in query['expected_entities'].items():
        extracted_value = extracted.get(entity_type)
        print(f"  Entity: {entity_type}")
        print(f"    Expected: {expected_value} (type: {type(expected_value).__name__})")
        print(f"    Extracted: {extracted_value} (type: {type(extracted_value).__name__ if extracted_value is not None else 'NoneType'})")
        
        # Check match
        if entity_type == "land_size_hectares":
            # Allow 5% tolerance for land
            if expected_value and extracted_value:
                tolerance = abs(expected_value) * 0.05
                match = abs(expected_value - extracted_value) <= tolerance
                print(f"    Match (5% tolerance): {match}")
        else:
            match = expected_value == extracted_value
            print(f"    Match (exact): {match}")

print("\n" + "="*80)
print("CHECKING EVALUATION SCRIPT")
print("="*80)

# Now test through orchestrator to see full pipeline
from app.services.language_service import LanguageService
from app.services.intent_router import IntentRouter

for query in test_queries[:2]:
    print(f"\nQuery: {query['message']}")
    
    # Detect language
    lang_service = LanguageService()
    language = lang_service.detect_language(query['message'])
    print(f"Detected language: {language}")
    
    # Detect intent
    intent, confidence, params = IntentRouter.detect_intent(query['message'], language=language)
    print(f"Detected intent: {intent}, confidence: {confidence}")
    
    # Extract entities
    entities = EntityExtractor.extract_all(query['message'], language=language)
    print(f"Extracted entities: {json.dumps(entities, indent=2)}")
    
    # Try to build farmer context (this is what orchestrator does)
    try:
        from app.models.farmer import FarmerContext
        farmer_context = FarmerContext(
            budget_rupees=entities.get("budget_rupees"),
            land_size_hectares=entities.get("land_size_hectares"),
            water_availability=entities.get("water_availability"),
            experience_level=entities.get("experience_level") or "beginner",
            location=entities.get("location"),
            income_goal_monthly=entities.get("income_goal_monthly"),
            time_availability=entities.get("time_availability"),
            risk_tolerance=entities.get("risk_tolerance"),
        )
        print(f"FarmerContext created: {farmer_context}")
    except Exception as e:
        print(f"Error creating FarmerContext: {e}")

print("\n" + "="*80)
print("END DEBUG")
print("="*80)
