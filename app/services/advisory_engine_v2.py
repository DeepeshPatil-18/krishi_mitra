"""Advisory Engine V2 - Improved enterprise recommendation engine"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

from app.services.scoring_system import (
    ScoringFactor,
    ScoringRules,
    RecommendationScore,
    FactorScore,
)
from app.services.data_provider import EnterpriseProvider
from app.schemas.advisory import FarmerContext, RecommendedEnterprise

logger = logging.getLogger(__name__)


class AdvisoryEngineV2:
    """
    Improved advisory engine that provides detailed, explainable recommendations.
    
    Uses deterministic scoring based on:
    - Budget fit
    - Land/space fit
    - Water availability fit
    - Experience level fit
    - Income goal fit
    - Risk tolerance fit
    - Time availability fit
    - Location fit (basic)
    - Resource fit
    """
    
    @staticmethod
    def evaluate_farmer(farmer_context: FarmerContext) -> List[RecommendedEnterprise]:
        """
        Evaluate a farmer against all enterprises and return ranked recommendations.
        
        Returns top 3 enterprises with detailed scoring breakdown.
        """
        
        # Get all enterprises to evaluate
        all_enterprises = EnterpriseProvider.get_all_enterprises()
        
        # Score farmer against each enterprise
        scores: List[Tuple[str, RecommendationScore]] = []
        
        for enterprise_data in all_enterprises:
            enterprise_code = enterprise_data.get("code")
            enterprise_name = enterprise_data.get("name_en")
            
            # Calculate score for this enterprise
            rec_score = AdvisoryEngineV2._score_enterprise(
                farmer_context=farmer_context,
                enterprise_data=enterprise_data
            )
            
            scores.append((enterprise_code, rec_score))
        
        # Sort by total score (descending)
        scores.sort(key=lambda x: x[1].total_score, reverse=True)
        
        # Convert to response format
        recommendations = []
        for idx, (enterprise_code, rec_score) in enumerate(scores[:3]):  # Top 3
            
            # Determine why this ranked higher than others
            why_ranked = None
            if idx == 0 and len(scores) > 1:
                next_enterprise = scores[1][1]
                score_diff = rec_score.total_score - next_enterprise.total_score
                why_ranked = AdvisoryEngineV2._explain_ranking(
                    rec_score,
                    next_enterprise,
                    score_diff
                )
            
            # Get additional data
            enterprise_data = next(
                (e for e in all_enterprises if e.get("code") == enterprise_code),
                {}
            )
            
            # Build response
            rec_response = RecommendedEnterprise(
                enterprise_code=enterprise_code,
                enterprise_name=enterprise_data.get("name_en", enterprise_code),
                suitability_score=round(rec_score.total_score, 1),
                factor_scores={
                    factor_name: {
                        "factor": factor_name,
                        "score": round(factor_score.score, 1),
                        "weight": factor_score.weight,
                        "explanation": factor_score.explanation,
                        "positive_indicators": factor_score.positive_indicators,
                        "negative_indicators": factor_score.negative_indicators,
                        "missing_data": factor_score.missing_data,
                    }
                    for factor_name, factor_score in rec_score.factor_scores.items()
                },
                primary_positive_factors=[
                    indicator for _, indicator in rec_score.primary_positive_factors
                ],
                primary_negative_factors=[
                    indicator for _, indicator in rec_score.primary_negative_factors
                ],
                estimated_investment_min=enterprise_data.get("estimated_investment", 20000),
                estimated_investment_max=None,  # Use same as min for now
                requirements=enterprise_data.get("requirements", []),
                risks=enterprise_data.get("risk_factors", []),
                training_recommendations=AdvisoryEngineV2._get_training_recommendations(
                    enterprise_code,
                    farmer_context.language if hasattr(farmer_context, 'language') else "marathi"
                ),
                relevant_schemes=AdvisoryEngineV2._get_relevant_schemes(
                    enterprise_code,
                    farmer_context.location or "maharashtra"
                ),
                potential_markets=AdvisoryEngineV2._get_potential_markets(enterprise_code),
                next_actions=AdvisoryEngineV2._get_next_actions(
                    enterprise_code,
                    enterprise_data
                ),
                why_ranked_higher=why_ranked
            )
            
            recommendations.append(rec_response)
        
        return recommendations
    
    @staticmethod
    def _score_enterprise(
        farmer_context: FarmerContext,
        enterprise_data: Dict
    ) -> RecommendationScore:
        """Calculate detailed score for farmer-enterprise fit"""
        
        enterprise_code = enterprise_data.get("code")
        enterprise_name = enterprise_data.get("name_en", enterprise_code)
        
        # Evaluate each factor
        factor_scores: Dict[str, FactorScore] = {}
        
        # Budget fit
        factor_scores["budget_fit"] = ScoringRules.evaluate_budget_fit(
            farmer_budget=farmer_context.budget_rupees,
            enterprise_min=enterprise_data.get("min_budget_rupees", 20000),
            enterprise_max=enterprise_data.get("max_budget_rupees")
        )
        
        # Land fit
        factor_scores["land_fit"] = ScoringRules.evaluate_land_fit(
            farmer_land=farmer_context.land_size_hectares,
            enterprise_min=enterprise_data.get("min_land_hectares", 0.1),
            enterprise_max=enterprise_data.get("max_land_hectares")
        )
        
        # Water fit
        factor_scores["water_fit"] = ScoringRules.evaluate_water_fit(
            farmer_water=farmer_context.water_availability,
            enterprise_requirement=enterprise_data.get("water_requirement", "medium")
        )
        
        # Experience fit
        factor_scores["experience_fit"] = ScoringRules.evaluate_experience_fit(
            farmer_experience=farmer_context.experience_level,
            enterprise_requirements=enterprise_data.get("requirements", [])
        )
        
        # Income fit
        factor_scores["income_fit"] = ScoringRules.evaluate_income_fit(
            farmer_income_goal=farmer_context.income_goal_monthly,
            enterprise_monthly_income=enterprise_data.get("estimated_income_monthly")
        )
        
        # Risk fit
        factor_scores["risk_fit"] = ScoringRules.evaluate_risk_fit(
            farmer_risk_tolerance=farmer_context.risk_tolerance or "medium",
            enterprise_risks=enterprise_data.get("risk_factors", [])
        )
        
        # Time fit
        factor_scores["time_fit"] = ScoringRules.evaluate_time_fit(
            farmer_time_available=farmer_context.time_availability
        )
        
        # Location fit (simple: prefer same state)
        location_score = 70.0  # Default neutral
        if farmer_context.location:
            # Simple check - in production could use scheme availability, climate, etc.
            location_score = 80.0
        
        factor_scores["location_fit"] = FactorScore(
            factor="location_fit",
            score=location_score,
            weight=0.10,
            explanation=f"Location: {farmer_context.location or 'not specified'}"
        )
        
        # Calculate total weighted score
        total_score = 0.0
        for factor_score in factor_scores.values():
            total_score += factor_score.weighted_contribution()
        
        # Calculate information completeness (0-1)
        # Based on how many optional fields were provided
        provided_fields = sum([
            farmer_context.land_size_hectares is not None,
            farmer_context.water_availability is not None,
            farmer_context.income_goal_monthly is not None,
            farmer_context.existing_resources is not None,
            farmer_context.electricity_available is not None,
            farmer_context.time_availability is not None,
            farmer_context.location is not None,
        ])
        total_optional_fields = 7
        information_completeness = min(1.0, 0.3 + (provided_fields / total_optional_fields) * 0.7)
        
        return RecommendationScore(
            enterprise_code=enterprise_code,
            enterprise_name=enterprise_name,
            total_score=total_score,
            factor_scores=factor_scores,
            information_completeness=information_completeness
        )
    
    @staticmethod
    def _explain_ranking(
        top_score: RecommendationScore,
        next_score: RecommendationScore,
        score_diff: float
    ) -> str:
        """Explain why top enterprise ranks higher than second"""
        
        if score_diff > 20:
            return f"{top_score.enterprise_name} is significantly better suited to your profile (score: {top_score.total_score:.0f} vs {next_score.total_score:.0f})"
        elif score_diff > 10:
            return f"{top_score.enterprise_name} is a better fit than {next_score.enterprise_name} for your context"
        else:
            return f"{top_score.enterprise_name} is slightly better than {next_score.enterprise_name}, but both are good options"
    
    @staticmethod
    def _get_training_recommendations(enterprise_code: str, language: str = "marathi") -> List[str]:
        """Get training modules for enterprise"""
        from app.services.data_provider import TrainingProvider
        
        modules = TrainingProvider.get_training_by_enterprise(enterprise_code, language)
        return [m.get("title", "") for m in modules[:3]]
    
    @staticmethod
    def _get_relevant_schemes(enterprise_code: str, state: str = "maharashtra") -> List[str]:
        """Get relevant schemes for enterprise"""
        from app.services.data_provider import SchemeProvider
        
        schemes = SchemeProvider.get_schemes_by_enterprise(enterprise_code, state)
        return [s.get("name", "") for s in schemes[:3]]
    
    @staticmethod
    def _get_potential_markets(enterprise_code: str) -> List[str]:
        """Get market opportunities for enterprise"""
        from app.services.data_provider import MarketProvider
        
        markets = MarketProvider.get_markets_by_enterprise(enterprise_code)
        return [m.get("location", "") for m in markets[:2]]
    
    @staticmethod
    def _get_next_actions(
        enterprise_code: str,
        enterprise_data: Dict
    ) -> List[str]:
        """Generate next action steps for farmer"""
        
        actions = []
        
        # Always start with verification
        actions.append("Confirm available space/resources for this enterprise")
        
        # Training
        actions.append("Enroll in basic training program")
        
        # Financial
        investment = enterprise_data.get("estimated_investment", 30000)
        actions.append(f"Estimate setup cost (approximately ₹{investment:,})")
        
        # Schemes
        actions.append("Check government scheme eligibility")
        
        # Market
        actions.append("Identify potential buyers in your area")
        
        # Pilot
        actions.append("Start with a small pilot batch")
        
        return actions[:5]  # Return top 5
    
    @staticmethod
    def _get_missing_information(farmer_context: FarmerContext) -> List[str]:
        """Identify missing information for better recommendations"""
        missing = []
        
        if farmer_context.land_size_hectares is None:
            missing.append("Available land/space size")
        
        if farmer_context.water_availability is None:
            missing.append("Water availability (high/medium/low)")
        
        if farmer_context.income_goal_monthly is None:
            missing.append("Monthly income goal")
        
        if farmer_context.existing_resources is None or not farmer_context.existing_resources:
            missing.append("Existing resources or infrastructure")
        
        if farmer_context.time_availability is None:
            missing.append("Time availability for enterprise")
        
        if farmer_context.location is None:
            missing.append("Specific location/state")
        
        return missing
