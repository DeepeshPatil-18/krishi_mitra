"""Advisory Service - wrapper around advisory engine with data provider integration"""

from typing import List, Optional, Dict, Any
import logging

from app.services.advisory_engine import AdvisoryEngine
from app.services.data_provider import (
    EnterpriseProvider, 
    SchemeProvider, 
    TrainingProvider,
    MarketProvider
)
from app.schemas.advisory import RecommendedEnterprise

logger = logging.getLogger(__name__)


class AdvisoryService:
    """
    Advisory service that wraps the advisory engine and enriches
    recommendations with data from providers.
    """
    
    @staticmethod
    def get_recommendations(
        budget_rupees: int,
        land_size_hectares: float,
        state: str,
        experience_level: str = "beginner",
        goals: Optional[str] = None,
    ) -> tuple[List[RecommendedEnterprise], str]:
        """
        Get enterprise recommendations with enriched data
        
        Returns:
            Tuple of (recommendations list, summary text)
        """
        
        # Get base recommendations from advisory engine
        base_recommendations = AdvisoryEngine.recommend_enterprises(
            budget_rupees=budget_rupees,
            land_size_hectares=land_size_hectares,
            state=state,
            experience_level=experience_level,
            goals=goals,
        )
        
        # Enrich each recommendation with actual data from providers
        enriched_recommendations = []
        for rec in base_recommendations:
            enriched = AdvisoryService._enrich_recommendation(
                rec, 
                state=state
            )
            enriched_recommendations.append(enriched)
        
        # Generate summary
        if enriched_recommendations:
            top_enterprise = enriched_recommendations[0].enterprise_name
            summary = (
                f"Based on your budget of ₹{budget_rupees:,} and {land_size_hectares} hectares of land, "
                f"we recommend {top_enterprise} as your best option. "
                f"This enterprise suits your profile well and has good market potential."
            )
        else:
            summary = "No suitable enterprises found for your current profile."
        
        return enriched_recommendations, summary
    
    @staticmethod
    def _enrich_recommendation(
        base_rec: RecommendedEnterprise,
        state: str = "maharashtra"
    ) -> RecommendedEnterprise:
        """Enrich a recommendation with real data from providers"""
        
        enterprise_code = base_rec.enterprise_code
        
        # Get relevant schemes
        schemes = SchemeProvider.get_schemes_by_enterprise(enterprise_code, state)
        scheme_names = [s.get("name") for s in schemes[:3]]
        
        # Get training modules
        training_modules = TrainingProvider.get_training_by_enterprise(enterprise_code)
        training_recs = [m.get("title") for m in training_modules[:2]]
        
        # Get market opportunities
        markets = MarketProvider.get_markets_by_enterprise(enterprise_code)
        market_info = [m.get("location") for m in markets[:2]]
        
        # Update recommendation with enriched data
        base_rec.relevant_schemes = scheme_names if scheme_names else base_rec.relevant_schemes
        base_rec.training_recommendations = training_recs if training_recs else base_rec.training_recommendations
        base_rec.potential_markets = market_info if market_info else base_rec.potential_markets
        
        return base_rec
    
    @staticmethod
    def get_enterprise_details(enterprise_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific enterprise"""
        return EnterpriseProvider.get_enterprise_by_code(enterprise_code)
    
    @staticmethod
    def get_schemes_for_enterprise(
        enterprise_code: str,
        state: str = "maharashtra"
    ) -> List[Dict[str, Any]]:
        """Get all schemes applicable to an enterprise"""
        return SchemeProvider.get_schemes_by_enterprise(enterprise_code, state)
    
    @staticmethod
    def get_training_for_enterprise(
        enterprise_code: str,
        language: str = "marathi"
    ) -> List[Dict[str, Any]]:
        """Get training modules for an enterprise"""
        return TrainingProvider.get_training_by_enterprise(enterprise_code, language)
    
    @staticmethod
    def get_markets_for_enterprise(enterprise_code: str) -> List[Dict[str, Any]]:
        """Get market opportunities for an enterprise"""
        return MarketProvider.get_markets_by_enterprise(enterprise_code)
