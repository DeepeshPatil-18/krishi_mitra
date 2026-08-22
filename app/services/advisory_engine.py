"""Advisory Engine - generates livelihood recommendations"""

import logging
from typing import List, Dict, Any, Optional
from app.schemas.advisory import RecommendedEnterprise

logger = logging.getLogger(__name__)


class AdvisoryEngine:
    """
    Generates livelihood recommendations based on farmer context.
    Uses explainable rules and scoring (not ML).
    """

    def __init__(self):
        pass

    @staticmethod
    def recommend_enterprises(
        budget_rupees: int,
        land_size_hectares: float,
        state: str,
        experience_level: str = "beginner",
        goals: Optional[str] = None,
    ) -> List[RecommendedEnterprise]:
        """
        Generate enterprise recommendations
        
        Args:
            budget_rupees: Farmer's available budget
            land_size_hectares: Land available
            state: State/location
            experience_level: Beginner, intermediate, expert
            goals: Farmer's goals
            
        Returns:
            List of recommended enterprises with scores
        """
        recommendations = []
        
        # Scoring factors
        # This is simplified; production would use more sophisticated logic
        
        enterprises = [
            {
                "code": "apiculture",
                "name": "Beekeeping",
                "min_budget": 20000,
                "max_budget": 500000,
                "min_land": 0.1,
                "max_land": 5.0,
                "investment": 40000,
                "monthly_income": 15000,
                "payback_months": 3,
            },
            {
                "code": "poultry",
                "name": "Poultry Farming",
                "min_budget": 30000,
                "max_budget": 200000,
                "min_land": 0.05,
                "max_land": 1.0,
                "investment": 50000,
                "monthly_income": 20000,
                "payback_months": 3,
            },
            {
                "code": "goat_farming",
                "name": "Goat Farming",
                "min_budget": 50000,
                "max_budget": 300000,
                "min_land": 0.5,
                "max_land": 2.0,
                "investment": 100000,
                "monthly_income": 25000,
                "payback_months": 5,
            },
            {
                "code": "mushroom",
                "name": "Mushroom Cultivation",
                "min_budget": 15000,
                "max_budget": 100000,
                "min_land": 0.01,
                "max_land": 0.2,
                "investment": 30000,
                "monthly_income": 12000,
                "payback_months": 3,
            },
            {
                "code": "vermicomposting",
                "name": "Vermicomposting",
                "min_budget": 10000,
                "max_budget": 80000,
                "min_land": 0.01,
                "max_land": 0.5,
                "investment": 20000,
                "monthly_income": 8000,
                "payback_months": 3,
            },
        ]
        
        for ent in enterprises:
            score = 0
            reasons = []
            
            # Budget fit
            if ent["min_budget"] <= budget_rupees <= ent["max_budget"]:
                score += 25
                reasons.append(f"Budget fits well (₹{ent['min_budget']} - ₹{ent['max_budget']})")
            elif budget_rupees >= ent["min_budget"]:
                score += 15
                reasons.append(f"Budget is sufficient (minimum ₹{ent['min_budget']})")
            else:
                score -= 10
                reasons.append(f"Budget may be tight (minimum ₹{ent['min_budget']})")
            
            # Land fit
            if ent["min_land"] <= land_size_hectares <= ent["max_land"]:
                score += 25
                reasons.append(f"Land size is ideal ({ent['min_land']}-{ent['max_land']} hectares)")
            elif land_size_hectares >= ent["min_land"]:
                score += 15
                reasons.append(f"Land is sufficient")
            
            # Experience level boost
            if experience_level == "beginner" and ent["investment"] < 50000:
                score += 10
                reasons.append("Good for beginners")
            
            # Ensure score is in valid range
            score = max(0, min(100, score))
            
            rec = RecommendedEnterprise(
                enterprise_code=ent["code"],
                enterprise_name=ent["name"],
                suitability_score=score,
                reasons=reasons,
                estimated_investment=ent["investment"],
                requirements=[
                    f"Minimum {ent['min_land']} hectares of land",
                    f"Initial capital of ₹{ent['investment']}",
                    "Basic farming knowledge",
                ],
                risks=[
                    "Market volatility",
                    "Seasonal variations",
                    "Disease management required",
                ],
                training_recommendations=[
                    f"Basic {ent['name']} setup",
                    "Pest management",
                    "Market linkage",
                ],
                relevant_schemes=[
                    "PM-KISAN",
                    "State-specific schemes",
                ],
                potential_markets=[
                    "Local markets",
                    "Cooperative societies",
                    "Direct buyers",
                ],
                next_actions=[
                    "Attend training program",
                    "Connect with local experts",
                    "Visit existing farms",
                    "Apply for government schemes",
                ],
            )
            
            recommendations.append(rec)
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
        
        return recommendations[:3]  # Return top 3 recommendations
