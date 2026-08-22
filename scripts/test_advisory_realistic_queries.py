"""
TASK 7: Test advisory with realistic farmer queries

Tests 10+ realistic scenarios covering:
- Budget constraints, land constraints
- Water availability, experience levels
- Multiple languages (Marathi, Hindi, English)
- Real farming interests
"""

from app.services.advisory_engine_v2 import AdvisoryEngineV2
from app.services.entity_extractor import EntityExtractor
from app.schemas.advisory import FarmerContext


def print_recommendation(query, context, recommendations):
    """Print a recommendation"""
    print(f"\nQUERY: {query}")
    print(f"Budget: Rs{context.budget_rupees:,}")
    if context.land_size_hectares:
        print(f"Land: {context.land_size_hectares} hectares")
    if context.water_availability:
        print(f"Water: {context.water_availability}")
    print(f"Experience: {context.experience_level}")
    
    print(f"\nTop Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec.enterprise_name} - Investment: Rs{rec.estimated_investment_min:,}")


def test_query_1():
    """Query 1: Low budget + small land + beginner"""
    context = FarmerContext(budget_rupees=20000, land_size_hectares=0.2, experience_level="beginner")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 1: Low Budget Small Land Beginner - PASS")


def test_query_2():
    """Query 2: Medium budget + medium land + intermediate + high water"""
    context = FarmerContext(budget_rupees=100000, land_size_hectares=1.5, water_availability="high", experience_level="intermediate")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 2: Medium Budget Medium Land Intermediate - PASS")


def test_query_3():
    """Query 3: Dairy interest + medium budget + experienced"""
    context = FarmerContext(budget_rupees=150000, land_size_hectares=2.0, experience_level="expert", water_availability="medium")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 3: Dairy Interest Experienced - PASS")


def test_query_4():
    """Query 4: Mushroom interest + low budget + no land"""
    context = FarmerContext(budget_rupees=25000, land_size_hectares=0.05, experience_level="beginner")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 4: Mushroom Low Budget Minimal Land - PASS")


def test_query_5():
    """Query 5: Part-time + low risk + limited budget"""
    context = FarmerContext(budget_rupees=40000, land_size_hectares=0.3, experience_level="beginner", time_availability="part_time", risk_tolerance="low")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 5: Part-Time Low Risk - PASS")


def test_query_6():
    """Query 6: Large land + high budget + experienced + high water"""
    context = FarmerContext(budget_rupees=300000, land_size_hectares=5.0, experience_level="expert", water_availability="high", time_availability="full_time")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 6: Large Land High Budget Experienced - PASS")


def test_query_7():
    """Query 7: Low water + medium budget + intermediate"""
    context = FarmerContext(budget_rupees=60000, land_size_hectares=2.0, experience_level="intermediate", water_availability="low")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 7: Low Water Medium Budget - PASS")


def test_query_8():
    """Query 8: Marathi query - low budget beginner"""
    query = "मला 30000 आहे आणि 0.5 हेक्टर जमीन आहे. मी नवीन शेतकरी आहे."
    entities = EntityExtractor.extract_all(query, language="marathi")
    context = FarmerContext(
        budget_rupees=entities.get("budget_rupees", 30000),
        land_size_hectares=entities.get("land_size_hectares", 0.5),
        experience_level=entities.get("experience_level", "beginner")
    )
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 8: Marathi Low Budget - PASS")


def test_query_9():
    """Query 9: Hindi query - medium budget intermediate"""
    query = "मेरे पास 100000 है, 1.5 हेक्टर जमीन है, और कुछ अनुभव है"
    entities = EntityExtractor.extract_all(query, language="hindi")
    context = FarmerContext(
        budget_rupees=entities.get("budget_rupees", 100000),
        land_size_hectares=entities.get("land_size_hectares", 1.5),
        experience_level=entities.get("experience_level", "intermediate")
    )
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 9: Hindi Medium Budget - PASS")


def test_query_10():
    """Query 10: Minimal information - only budget"""
    context = FarmerContext(budget_rupees=75000, land_size_hectares=None, experience_level="beginner")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 10: Minimal Info - PASS")


def test_query_11():
    """Query 11: Conflict - high income goal but low budget"""
    context = FarmerContext(budget_rupees=30000, land_size_hectares=0.2, income_goal_monthly=100000, experience_level="beginner")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 11: Conflicting Constraints - PASS")


def test_query_12():
    """Query 12: Part-time + high risk tolerance"""
    context = FarmerContext(budget_rupees=80000, land_size_hectares=1.0, experience_level="intermediate", time_availability="part_time", risk_tolerance="high")
    recommendations = AdvisoryEngineV2.evaluate_farmer(context)
    assert len(recommendations) > 0
    print("Query 12: Part-Time High Risk - PASS")


def main():
    """Run all realistic query tests"""
    print("\n" + "="*80)
    print("TASK 7: FARMER ADVISORY - REALISTIC QUERY EVALUATION")
    print("="*80 + "\n")
    
    tests = [
        test_query_1, test_query_2, test_query_3, test_query_4,
        test_query_5, test_query_6, test_query_7, test_query_8,
        test_query_9, test_query_10, test_query_11, test_query_12
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"FAIL: {test_fn.__name__}: {str(e)}")
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
