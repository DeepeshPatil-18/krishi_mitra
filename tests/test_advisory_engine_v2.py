"""Tests for Advisory Engine V2"""

import pytest
from app.services.advisory_engine_v2 import AdvisoryEngineV2
from app.schemas.advisory import FarmerContext


class TestAdvisoryEngineV2:
    """Test Advisory Engine V2 scoring and recommendations"""
    
    def test_high_budget_farmer(self):
        """Test recommendation for high-budget farmer"""
        context = FarmerContext(
            budget_rupees=200000,
            land_size_hectares=5.0,
            location="maharashtra",
            experience_level="intermediate",
            water_availability="high"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        assert len(recommendations) <= 3
        assert all(0 <= rec.suitability_score <= 100 for rec in recommendations)
        # First should be better than second
        assert recommendations[0].suitability_score >= recommendations[-1].suitability_score
    
    def test_low_budget_farmer(self):
        """Test recommendation for low-budget farmer"""
        context = FarmerContext(
            budget_rupees=15000,
            land_size_hectares=0.1,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Low budget enterprises should rank higher
        top_investment = recommendations[0].estimated_investment_min
        assert top_investment <= 50000, "Top recommendation should be low-cost"
    
    def test_limited_land_farmer(self):
        """Test recommendation for farmer with limited land"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=0.05,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Mushroom or vermicomposting should rank high (small space)
        top_codes = [rec.enterprise_code for rec in recommendations[:2]]
        assert any(code in top_codes for code in ["mushroom", "vermicomposting"])
    
    def test_limited_water_farmer(self):
        """Test recommendation for farmer with low water availability"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            water_availability="low",
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Should recommend low-water enterprises
        # Vermicomposting, apiculture have low water requirements
        top_codes = [rec.enterprise_code for rec in recommendations[:2]]
        assert any(code in top_codes for code in ["vermicomposting", "apiculture"])
    
    def test_beginner_farmer(self):
        """Test recommendation for beginner"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # All should have decent beginner-friendly scores
        assert all(rec.suitability_score > 30 for rec in recommendations)
    
    def test_experienced_farmer(self):
        """Test recommendation for experienced farmer"""
        context = FarmerContext(
            budget_rupees=100000,
            land_size_hectares=5.0,
            experience_level="expert"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Expert farmer should get higher scores overall
        avg_score = sum(rec.suitability_score for rec in recommendations) / len(recommendations)
        assert avg_score > 60
    
    def test_farmer_with_existing_livestock(self):
        """Test recommendation for farmer with livestock infrastructure"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=1.0,
            existing_resources=["shed", "livestock"],
            experience_level="intermediate"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Should recommend poultry, goat farming (need shed)
        top_codes = [rec.enterprise_code for rec in recommendations[:2]]
        assert any(code in top_codes for code in ["poultry", "goat_farming"])
    
    def test_income_goal_fit(self):
        """Test income goal consideration"""
        context_low_goal = FarmerContext(
            budget_rupees=30000,
            land_size_hectares=0.5,
            income_goal_monthly=5000,
            experience_level="beginner"
        )
        
        context_high_goal = FarmerContext(
            budget_rupees=30000,
            land_size_hectares=0.5,
            income_goal_monthly=50000,
            experience_level="beginner"
        )
        
        recs_low = AdvisoryEngineV2.evaluate_farmer(context_low_goal)
        recs_high = AdvisoryEngineV2.evaluate_farmer(context_high_goal)
        
        assert len(recs_low) > 0
        assert len(recs_high) > 0
        # Both should return recommendations but may differ in order
        assert recs_low[0].enterprise_code in [r.enterprise_code for r in recs_high]
    
    def test_partial_information(self):
        """Test with minimal/partial information"""
        context = FarmerContext(
            budget_rupees=50000
            # Everything else optional/None
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Should still work and explain missing data
        for rec in recommendations:
            # Should identify missing information
            if rec.factor_scores:
                has_missing = any(
                    score.get("missing_data", [])
                    for score in rec.factor_scores.values()
                )
                # Expect missing data indicators
                assert has_missing or rec.suitability_score > 0
    
    def test_all_six_enterprises_evaluated(self):
        """Test that all 6 enterprises are evaluated"""
        context = FarmerContext(
            budget_rupees=100000,
            land_size_hectares=3.0,
            experience_level="intermediate"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        # Should return top 3 of 6
        assert len(recommendations) <= 3
        
        expected_enterprises = {
            "apiculture", "poultry", "fisheries",
            "goat_farming", "mushroom", "vermicomposting"
        }
        
        # Top 3 should be from the 6 expected
        recommended_codes = {rec.enterprise_code for rec in recommendations}
        assert recommended_codes.issubset(expected_enterprises)
    
    def test_deterministic_scoring(self):
        """Test that scoring is deterministic"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            water_availability="medium",
            experience_level="beginner"
        )
        
        # Run twice
        recs1 = AdvisoryEngineV2.evaluate_farmer(context)
        recs2 = AdvisoryEngineV2.evaluate_farmer(context)
        
        # Should get same results
        assert len(recs1) == len(recs2)
        for r1, r2 in zip(recs1, recs2):
            assert r1.enterprise_code == r2.enterprise_code
            assert r1.suitability_score == r2.suitability_score
    
    def test_score_breakdown_provided(self):
        """Test that factor scores are provided"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=1.0,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Should have factor scores
        assert rec.factor_scores is not None
        assert len(rec.factor_scores) > 0
        
        # Each factor should have details
        for factor_name, factor_score in rec.factor_scores.items():
            assert "score" in factor_score
            assert "weight" in factor_score
            assert "explanation" in factor_score
            assert 0 <= factor_score["score"] <= 100
    
    def test_positive_negative_factors(self):
        """Test that positive and negative factors are identified"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Should identify positives
        assert rec.primary_positive_factors is not None
        assert len(rec.primary_positive_factors) > 0
    
    def test_training_recommendations_connected(self):
        """Test that training modules are connected"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=0.1,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Should have training recommendations
        assert rec.training_recommendations is not None
        # Mushroom cultivation should have training
        if rec.enterprise_code == "mushroom":
            assert len(rec.training_recommendations) > 0
    
    def test_scheme_recommendations_connected(self):
        """Test that schemes are connected"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            location="maharashtra",
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Should have scheme recommendations
        assert rec.relevant_schemes is not None
    
    def test_market_opportunities_connected(self):
        """Test that market data is connected"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Should have market opportunities
        assert rec.potential_markets is not None
    
    def test_missing_information_identified(self):
        """Test that missing information is identified"""
        context = FarmerContext(
            budget_rupees=50000
            # Missing everything else
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        
        # Missing information should be identified in factor scores
        missing_data_found = []
        for rec in recommendations:
            for factor_score in rec.factor_scores.values():
                missing_data_found.extend(factor_score.get("missing_data", []))
        
        # Should have identified missing data
        assert len(missing_data_found) > 0
    
    def test_information_completeness_score(self):
        """Test information completeness indicator"""
        context_minimal = FarmerContext(budget_rupees=50000)
        
        context_complete = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            water_availability="medium",
            location="maharashtra",
            experience_level="intermediate",
            income_goal_monthly=20000,
            time_availability="full_time",
            existing_resources=["shed"]
        )
        
        recs_minimal = AdvisoryEngineV2.evaluate_farmer(context_minimal)
        recs_complete = AdvisoryEngineV2.evaluate_farmer(context_complete)
        
        # Both should return recommendations
        assert len(recs_minimal) > 0
        assert len(recs_complete) > 0
    
    def test_multilingual_training_request(self):
        """Test that training recommendations work across languages"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=0.1,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        # Should still get recommendations (language is handled in API layer)
        assert recommendations[0].training_recommendations is not None
    
    def test_ranking_explanation_provided(self):
        """Test that ranking explanation is provided"""
        context = FarmerContext(
            budget_rupees=50000,
            land_size_hectares=2.0,
            experience_level="beginner"
        )
        
        recommendations = AdvisoryEngineV2.evaluate_farmer(context)
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Top recommendation should have explanation
        assert rec.why_ranked_higher is not None or len(recommendations) == 1


class TestScoringFactors:
    """Test individual scoring factors"""
    
    def test_budget_fit_perfect_match(self):
        """Test budget scoring when perfectly matched"""
        from app.services.scoring_system import ScoringRules
        
        score = ScoringRules.evaluate_budget_fit(
            farmer_budget=50000,
            enterprise_min=40000,
            enterprise_max=60000
        )
        
        assert score.score == 100
        assert len(score.positive_indicators) > 0
    
    def test_budget_fit_below_minimum(self):
        """Test budget scoring when below minimum"""
        from app.services.scoring_system import ScoringRules
        
        score = ScoringRules.evaluate_budget_fit(
            farmer_budget=10000,
            enterprise_min=20000
        )
        
        assert score.score < 50
        assert len(score.negative_indicators) > 0
    
    def test_land_fit_optimal(self):
        """Test land scoring when optimal"""
        from app.services.scoring_system import ScoringRules
        
        score = ScoringRules.evaluate_land_fit(
            farmer_land=2.0,
            enterprise_min=0.5,
            enterprise_max=3.0
        )
        
        assert score.score > 75
    
    def test_experience_fit(self):
        """Test experience level scoring"""
        from app.services.scoring_system import ScoringRules
        
        score_beginner = ScoringRules.evaluate_experience_fit("beginner")
        score_expert = ScoringRules.evaluate_experience_fit("expert")
        
        assert score_beginner.score < score_expert.score
    
    def test_water_fit_exact_match(self):
        """Test water availability matching"""
        from app.services.scoring_system import ScoringRules
        
        score = ScoringRules.evaluate_water_fit("medium", "medium")
        
        assert score.score > 80
