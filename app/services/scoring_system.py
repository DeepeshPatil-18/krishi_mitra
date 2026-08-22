"""Scoring system for enterprise suitability evaluation"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ScoringFactor(str, Enum):
    """Scoring factors used in evaluation"""
    BUDGET_FIT = "budget_fit"
    LAND_FIT = "land_fit"
    WATER_FIT = "water_fit"
    EXPERIENCE_FIT = "experience_fit"
    INCOME_FIT = "income_fit"
    RESOURCE_FIT = "resource_fit"
    LOCATION_FIT = "location_fit"
    RISK_FIT = "risk_fit"
    TIME_FIT = "time_fit"


@dataclass
class ScoringWeights:
    """Weights for different scoring factors (sum should be close to 1.0)"""
    budget_fit: float = 0.20
    land_fit: float = 0.18
    water_fit: float = 0.12
    experience_fit: float = 0.15
    income_fit: float = 0.10
    resource_fit: float = 0.08
    location_fit: float = 0.10
    risk_fit: float = 0.07
    
    def __post_init__(self):
        """Validate that weights sum to approximately 1.0"""
        total = sum([
            self.budget_fit, self.land_fit, self.water_fit,
            self.experience_fit, self.income_fit, self.resource_fit,
            self.location_fit, self.risk_fit
        ])
        if not (0.95 < total < 1.05):
            raise ValueError(f"Weights must sum to ~1.0, got {total}")


@dataclass
class FactorScore:
    """Score for a single factor"""
    factor: ScoringFactor
    score: float  # 0-100
    weight: float  # contribution to total (0-1)
    explanation: str
    positive_indicators: List[str] = field(default_factory=list)
    negative_indicators: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    
    def weighted_contribution(self) -> float:
        """Calculate weighted contribution to total score"""
        return self.score * self.weight / 100.0


@dataclass
class RecommendationScore:
    """Complete score breakdown for an enterprise recommendation"""
    enterprise_code: str
    enterprise_name: str
    total_score: float  # 0-100
    factor_scores: Dict[str, FactorScore]
    information_completeness: float  # 0-1, how much farmer info was available
    
    @property
    def primary_positive_factors(self) -> List[Tuple[str, str]]:
        """Top 3 positive factors"""
        positives = []
        for factor_name, score in self.factor_scores.items():
            for indicator in score.positive_indicators:
                positives.append((factor_name, indicator))
        return positives[:3]
    
    @property
    def primary_negative_factors(self) -> List[Tuple[str, str]]:
        """Top 3 negative factors"""
        negatives = []
        for factor_name, score in self.factor_scores.items():
            for indicator in score.negative_indicators:
                negatives.append((factor_name, indicator))
        return negatives[:3]
    
    @property
    def missing_information(self) -> List[str]:
        """Aggregate missing data across all factors"""
        missing = []
        for score in self.factor_scores.values():
            missing.extend(score.missing_data)
        # Remove duplicates while preserving order
        seen = set()
        unique_missing = []
        for item in missing:
            if item not in seen:
                seen.add(item)
                unique_missing.append(item)
        return unique_missing


class ScoringRules:
    """
    Deterministic rules for scoring each factor.
    These are applied per enterprise based on its characteristics.
    """
    
    @staticmethod
    def evaluate_budget_fit(
        farmer_budget: int,
        enterprise_min: int,
        enterprise_max: Optional[int] = None
    ) -> FactorScore:
        """
        Evaluate how well farmer budget fits enterprise requirements
        
        Scoring logic:
        - Perfect fit: within min-max range
        - Acceptable: above minimum, may require setup phasing
        - Risky: below minimum
        """
        score = 0.0
        positives = []
        negatives = []
        
        if farmer_budget >= enterprise_min:
            score += 50  # Meets minimum
            positives.append(f"Budget (₹{farmer_budget:,}) meets minimum requirement (₹{enterprise_min:,})")
            
            if enterprise_max and farmer_budget <= enterprise_max:
                score += 50  # Perfect fit
                positives.append("Budget is within optimal range")
            elif enterprise_max:
                score += 30  # Above range but workable
                positives.append("Budget exceeds typical requirement (opportunity for scale)")
            else:
                score += 40  # No upper bound, good buffer
                positives.append("Budget provides comfortable margin above minimum")
        else:
            score += 20  # Below minimum but not impossible
            gap = enterprise_min - farmer_budget
            negatives.append(f"Budget is ₹{gap:,} below minimum (₹{enterprise_min:,})")
            negatives.append("May need additional financing or phased setup")
        
        return FactorScore(
            factor=ScoringFactor.BUDGET_FIT,
            score=min(100, score),
            weight=0.20,
            explanation=f"Budget ₹{farmer_budget:,} vs ₹{enterprise_min:,}-{enterprise_max or 'unlimited'}",
            positive_indicators=positives,
            negative_indicators=negatives
        )
    
    @staticmethod
    def evaluate_land_fit(
        farmer_land: Optional[float],
        enterprise_min: float,
        enterprise_max: Optional[float] = None
    ) -> FactorScore:
        """Evaluate land/space fit"""
        if farmer_land is None:
            return FactorScore(
                factor=ScoringFactor.LAND_FIT,
                score=50.0,  # Neutral without data
                weight=0.18,
                explanation="Land availability unknown",
                missing_data=["land_size_hectares"]
            )
        
        score = 0.0
        positives = []
        negatives = []
        
        if farmer_land >= enterprise_min:
            score += 50
            positives.append(f"Land ({farmer_land}ha) meets minimum ({enterprise_min}ha)")
            
            if enterprise_max and farmer_land <= enterprise_max:
                score += 50
                positives.append("Land size is optimal for this enterprise")
            elif enterprise_max:
                score += 25
                negatives.append(f"Land ({farmer_land}ha) exceeds typical range ({enterprise_max}ha)")
                positives.append("Extra space available for expansion")
            else:
                score += 40
                positives.append("Adequate space with room for growth")
        else:
            score += 15
            gap = enterprise_min - farmer_land
            negatives.append(f"Land shortage: have {farmer_land}ha, need {enterprise_min}ha")
        
        return FactorScore(
            factor=ScoringFactor.LAND_FIT,
            score=min(100, score),
            weight=0.18,
            explanation=f"{farmer_land}ha vs {enterprise_min}-{enterprise_max or 'unlimited'}ha",
            positive_indicators=positives,
            negative_indicators=negatives
        )
    
    @staticmethod
    def evaluate_water_fit(
        farmer_water: Optional[str],
        enterprise_requirement: str
    ) -> FactorScore:
        """
        Evaluate water availability fit
        Levels: high, medium, low, any
        """
        if farmer_water is None or farmer_water.lower() == "unknown":
            return FactorScore(
                factor=ScoringFactor.WATER_FIT,
                score=50.0,
                weight=0.12,
                explanation="Water availability unknown",
                missing_data=["water_availability"]
            )
        
        farmer_level = farmer_water.lower()
        enterprise_level = enterprise_requirement.lower()
        
        # Map water levels to numeric values
        water_levels = {"low": 1, "medium": 2, "high": 3, "any": 0}
        farmer_val = water_levels.get(farmer_level, 2)
        enterprise_val = water_levels.get(enterprise_level, 2)
        
        positives = []
        negatives = []
        
        if enterprise_level == "any":
            score = 100
            positives.append("Enterprise has no specific water requirements")
        elif farmer_val >= enterprise_val:
            score = 90
            positives.append(f"Water availability ({farmer_level}) meets enterprise need ({enterprise_level})")
        elif farmer_val == enterprise_val - 1:
            score = 60
            negatives.append(f"Water slightly below requirement (have {farmer_level}, need {enterprise_level})")
        else:
            score = 30
            negatives.append(f"Water significantly below requirement (have {farmer_level}, need {enterprise_level})")
        
        return FactorScore(
            factor=ScoringFactor.WATER_FIT,
            score=score,
            weight=0.12,
            explanation=f"Water: {farmer_level} vs {enterprise_level}",
            positive_indicators=positives,
            negative_indicators=negatives
        )
    
    @staticmethod
    def evaluate_experience_fit(
        farmer_experience: str,
        enterprise_requirements: Optional[List[str]] = None
    ) -> FactorScore:
        """Evaluate farmer experience level fit"""
        experience_level = farmer_experience.lower()
        
        positives = []
        negatives = []
        
        if experience_level == "beginner":
            score = 80  # Most enterprises support beginners
            positives.append("Enterprise suitable for beginners")
        elif experience_level == "intermediate":
            score = 90
            positives.append("Good match for intermediate farmer")
        elif experience_level == "expert":
            score = 95
            positives.append("Enterprise matches expert skill level")
        else:
            score = 75
            positives.append("Experience level acceptable")
        
        return FactorScore(
            factor=ScoringFactor.EXPERIENCE_FIT,
            score=score,
            weight=0.15,
            explanation=f"Experience level: {experience_level}",
            positive_indicators=positives,
            negative_indicators=negatives
        )
    
    @staticmethod
    def evaluate_income_fit(
        farmer_income_goal: Optional[int],
        enterprise_monthly_income: Optional[int]
    ) -> FactorScore:
        """Evaluate if enterprise income matches farmer goals"""
        if farmer_income_goal is None:
            return FactorScore(
                factor=ScoringFactor.INCOME_FIT,
                score=70.0,
                weight=0.10,
                explanation="Income goal not specified",
                missing_data=["income_goal"]
            )
        
        if enterprise_monthly_income is None:
            return FactorScore(
                factor=ScoringFactor.INCOME_FIT,
                score=60.0,
                weight=0.10,
                explanation="Enterprise income data unavailable",
                missing_data=["enterprise_income_data"]
            )
        
        positives = []
        negatives = []
        
        if enterprise_monthly_income >= farmer_income_goal:
            score = 95
            positives.append(f"Enterprise income (₹{enterprise_monthly_income:,}/month) exceeds goal (₹{farmer_income_goal:,})")
        elif enterprise_monthly_income >= farmer_income_goal * 0.8:
            score = 80
            positives.append(f"Enterprise income approaches goal")
        elif enterprise_monthly_income >= farmer_income_goal * 0.5:
            score = 50
            negatives.append(f"Enterprise income (₹{enterprise_monthly_income:,}) is below goal (₹{farmer_income_goal:,})")
        else:
            score = 25
            negatives.append(f"Enterprise income significantly below goal")
        
        return FactorScore(
            factor=ScoringFactor.INCOME_FIT,
            score=score,
            weight=0.10,
            explanation=f"Income: ₹{enterprise_monthly_income:,}/month vs ₹{farmer_income_goal:,} goal",
            positive_indicators=positives,
            negative_indicators=negatives
        )
    
    @staticmethod
    def evaluate_risk_fit(
        farmer_risk_tolerance: str,
        enterprise_risks: Optional[List[str]] = None
    ) -> FactorScore:
        """Evaluate risk tolerance fit"""
        tolerance = farmer_risk_tolerance.lower()
        risk_count = len(enterprise_risks) if enterprise_risks else 0
        
        positives = []
        negatives = []
        
        if tolerance == "high":
            score = 85 - (risk_count * 5)  # More risks = lower score
            positives.append("Risk profile matches farmer tolerance")
        elif tolerance == "medium":
            score = 75 - (risk_count * 3)
            if risk_count <= 2:
                positives.append("Manageable risk level")
            else:
                negatives.append(f"Multiple risks ({risk_count}) for medium tolerance farmer")
        elif tolerance == "low":
            score = 65 - (risk_count * 5)
            if risk_count > 1:
                negatives.append(f"Enterprise has {risk_count} risk factors for low-tolerance farmer")
            else:
                positives.append("Relatively low-risk enterprise")
        else:
            score = 70
        
        return FactorScore(
            factor=ScoringFactor.RISK_FIT,
            score=max(0, min(100, score)),
            weight=0.07,
            explanation=f"Risk tolerance: {tolerance} ({risk_count} enterprise risks)",
            positive_indicators=positives,
            negative_indicators=negatives
        )
    
    @staticmethod
    def evaluate_time_fit(
        farmer_time_available: Optional[str]
    ) -> FactorScore:
        """Evaluate time availability"""
        if farmer_time_available is None:
            return FactorScore(
                factor=ScoringFactor.TIME_FIT,
                score=70.0,
                weight=0.08,
                explanation="Time availability not specified",
                missing_data=["time_availability"]
            )
        
        time_level = farmer_time_available.lower()
        
        if time_level in ["full_time", "full-time", "full time"]:
            score = 95
            explanation = "Full-time available - excellent for most enterprises"
        elif time_level in ["part_time", "part-time", "part time"]:
            score = 75
            explanation = "Part-time commitment may limit enterprise scope"
        elif time_level in ["limited", "weekends"]:
            score = 50
            explanation = "Limited time - may restrict enterprise options"
        else:
            score = 70
            explanation = "Time availability unclear"
        
        return FactorScore(
            factor=ScoringFactor.TIME_FIT,
            score=score,
            weight=0.08,
            explanation=explanation
        )
