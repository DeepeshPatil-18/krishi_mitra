"""Tests for advisory engine"""

import pytest
from app.services.advisory_engine import AdvisoryEngine


def test_recommend_enterprises_basic():
    """Test basic enterprise recommendation"""
    recommendations = AdvisoryEngine.recommend_enterprises(
        budget_rupees=50000,
        land_size_hectares=2.0,
        state="maharashtra",
        experience_level="beginner",
    )
    
    assert len(recommendations) > 0
    assert all(0 <= rec.suitability_score <= 100 for rec in recommendations)
    
    # First recommendation should have highest score
    assert recommendations[0].suitability_score >= recommendations[-1].suitability_score


def test_recommend_enterprises_low_budget():
    """Test recommendation with low budget"""
    recommendations = AdvisoryEngine.recommend_enterprises(
        budget_rupees=15000,
        land_size_hectares=0.1,
        state="maharashtra",
    )
    
    # Should still return recommendations
    assert len(recommendations) > 0
    
    # Lower budget enterprises should rank higher
    for rec in recommendations[:1]:
        assert rec.estimated_investment <= 50000


def test_recommend_enterprises_large_land():
    """Test recommendation with large land"""
    recommendations = AdvisoryEngine.recommend_enterprises(
        budget_rupees=200000,
        land_size_hectares=5.0,
        state="maharashtra",
    )
    
    assert len(recommendations) > 0
    assert all(rec.suitability_score > 0 for rec in recommendations)


def test_recommendations_have_required_fields():
    """Test that recommendations have all required fields"""
    recommendations = AdvisoryEngine.recommend_enterprises(
        budget_rupees=50000,
        land_size_hectares=2.0,
        state="maharashtra",
    )
    
    for rec in recommendations:
        assert rec.enterprise_code is not None
        assert rec.enterprise_name is not None
        assert len(rec.reasons) > 0
        assert rec.estimated_investment > 0
        assert len(rec.requirements) > 0
        assert len(rec.risks) > 0
        assert len(rec.next_actions) > 0
