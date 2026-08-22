"""
Scheme Search Service — Deterministic search and ranking for farmer government schemes.

Uses verified scheme dataset from chatgpt_files/krishimitra_scheme_dataset_v1.json
Implements keyword search, category matching, farmer entity matching, and location awareness.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SchemeResult:
    """Ranked scheme result with relevance score"""
    scheme: Dict[str, Any]
    relevance_score: float
    match_signals: List[str]  # For debugging: which signals matched


class SchemeService:
    """Service for searching and ranking government schemes based on farmer queries"""

    # Load dataset once on module import
    _SCHEMES_CACHE = None

    @classmethod
    def _load_schemes(cls) -> List[Dict[str, Any]]:
        """Load scheme dataset from verified JSON file"""
        if cls._SCHEMES_CACHE is not None:
            return cls._SCHEMES_CACHE

        file_path = Path(__file__).parent.parent.parent / "chatgpt_files" / "krishimitra_scheme_dataset_v1.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls._SCHEMES_CACHE = data.get("schemes", [])
                logger.info(f"Loaded {len(cls._SCHEMES_CACHE)} schemes from {file_path}")
                return cls._SCHEMES_CACHE
        except FileNotFoundError:
            logger.error(f"Scheme dataset not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in scheme dataset: {e}")
            return []

    @classmethod
    def search_schemes(
        cls,
        query: str = "",
        location: Optional[str] = None,
        enterprise: Optional[str] = None,
        extracted_entities: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[SchemeResult]:
        """
        Search and rank schemes based on query and farmer context.

        Args:
            query: Free-text search query (farmer message)
            location: Farmer location (e.g., "maharashtra", "nashik")
            enterprise: Enterprise type (e.g., "goat", "mushroom")
            extracted_entities: Full extracted entities dict (includes water, land, experience, etc.)
            limit: Max number of results to return

        Returns:
            List of SchemeResult ranked by relevance (highest first)
        """
        schemes = cls._load_schemes()
        if not schemes:
            logger.warning("No schemes loaded; returning empty results")
            return []

        # Normalize inputs
        query_lower = query.lower() if query else ""
        location_lower = location.lower() if location else "maharashtra"  # Default to Maharashtra
        enterprise_lower = enterprise.lower() if enterprise else ""
        
        # Score each scheme
        scored_schemes: List[Tuple[SchemeResult, float]] = []
        
        for scheme in schemes:
            score, signals = cls._score_scheme(
                scheme=scheme,
                query_lower=query_lower,
                location_lower=location_lower,
                enterprise_lower=enterprise_lower,
                extracted_entities=extracted_entities or {}
            )
            
            if score > 0:  # Only include schemes with at least some match
                result = SchemeResult(scheme=scheme, relevance_score=score, match_signals=signals)
                scored_schemes.append((result, score))

        # Sort by relevance (highest first)
        scored_schemes.sort(key=lambda x: x[1], reverse=True)

        # Return top N results (without the score tuple wrapper)
        return [result for result, _ in scored_schemes[:limit]]

    @classmethod
    def _score_scheme(
        cls,
        scheme: Dict[str, Any],
        query_lower: str,
        location_lower: str,
        enterprise_lower: str,
        extracted_entities: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Score a single scheme based on relevance signals.
        
        Returns:
            (relevance_score, list_of_signals_that_matched)
        """
        score = 0.0
        signals = []

        # Extract scheme info
        scheme_name = scheme.get("name", "").lower()
        scheme_keywords = [kw.lower() for kw in scheme.get("keywords", [])]
        scheme_category = scheme.get("category", "").lower()
        scheme_scope = scheme.get("scope", "").lower()

        # Signal 1: Keyword match in query (highest weight)
        keyword_match_count = 0
        for keyword in scheme_keywords:
            if keyword in query_lower or query_lower in keyword:
                keyword_match_count += 1
        if keyword_match_count > 0:
            score += 50.0  # High weight for direct keyword match
            signals.append(f"keyword_match({keyword_match_count})")

        # Signal 2: Scheme name match in query
        if scheme_name in query_lower:
            score += 30.0
            signals.append("scheme_name_match")

        # Signal 3: Category match with extracted enterprise
        if enterprise_lower:
            enterprise_keywords = cls._get_category_keywords(enterprise_lower)
            if scheme_category in enterprise_keywords:
                score += 25.0
                signals.append(f"category_match_enterprise({enterprise_lower})")

        # Signal 4: Water availability matching irrigation schemes
        if extracted_entities.get("water_availability") == "low":
            if scheme_category in ["irrigation", "water_management", "solar_irrigation"]:
                score += 20.0
                signals.append("low_water_irrigation_match")

        # Signal 5: Land size matching certain categories
        land_size = extracted_entities.get("land_size_hectares")
        if land_size:
            if land_size < 1 and scheme_category in ["horticulture", "food_processing", "beekeeping"]:
                score += 15.0
                signals.append("small_land_match")
            elif land_size >= 2 and scheme_category in ["crop_production", "food_grains", "oilseeds"]:
                score += 10.0
                signals.append("medium_land_crop_match")

        # Signal 6: Location preference (Maharashtra schemes when in Maharashtra)
        if location_lower in ["maharashtra", "nashik", "pune", "aurangabad"]:
            if scheme_scope == "maharashtra":
                score += 20.0
                signals.append("maharashtra_location_match")
            elif scheme_scope == "central":
                score += 5.0  # Small boost for central schemes even when in Maharashtra

        # Signal 7: Training/capacity building for beginners
        if extracted_entities.get("experience_level") == "beginner":
            if scheme_category in ["training", "farmer_organization", "knowledge"]:
                score += 15.0
                signals.append("beginner_training_match")

        # Signal 8: Livestock/livestock-adjacent categories
        livestock_keywords = ["goat", "sheep", "cattle", "poultry", "dairy", "apiculture", "fisheries"]
        if any(kw in enterprise_lower for kw in livestock_keywords):
            if scheme_category in ["livestock", "dairy", "beekeeping", "fisheries", "animal_husbandry_infrastructure"]:
                score += 20.0
                signals.append("livestock_enterprise_match")

        # Signal 9: Query mentions "scheme" or "yogna" (intent confirmation)
        if "scheme" in query_lower or "yogna" in query_lower or "योजना" in query_lower:
            score += 5.0
            signals.append("scheme_intent_confirmed")

        return score, signals

    @classmethod
    def _get_category_keywords(cls, enterprise: str) -> List[str]:
        """Map enterprise to relevant scheme categories"""
        enterprise_lower = enterprise.lower()
        
        category_map = {
            "mushroom": ["horticulture", "food_processing"],
            "goat": ["livestock", "animal_husbandry_infrastructure"],
            "sheep": ["livestock", "animal_husbandry_infrastructure"],
            "cattle": ["dairy", "livestock"],
            "poultry": ["livestock"],
            "apiculture": ["beekeeping"],
            "honey": ["beekeeping"],
            "fisheries": ["fisheries"],
            "fish": ["fisheries"],
            "vegetable": ["horticulture", "crop_production"],
            "fruit": ["horticulture"],
            "spice": ["horticulture"],
            "rice": ["crop_production", "food_grains"],
            "wheat": ["crop_production", "food_grains"],
            "pulse": ["crop_production", "food_grains"],
            "dal": ["crop_production", "food_grains"],
            "oilseed": ["oilseeds", "crop_production"],
            "cotton": ["crop_production"],
            "sugarcane": ["crop_production"],
        }
        
        for key, categories in category_map.items():
            if key in enterprise_lower:
                return categories
        
        return []

    @classmethod
    def format_results(cls, results: List[SchemeResult], language: str = "english") -> str:
        """
        Format scheme results into farmer-friendly text.
        
        Args:
            results: List of SchemeResult ranked by relevance
            language: "english", "hindi", or "marathi"
        
        Returns:
            Formatted response string
        """
        if not results:
            if language == "marathi":
                return "खेदाची गोष्ट! तुमच्या क्वेरीशी संबंधित कोणती योजना सापडली नाही. कृपया तुमचे तपशील (जमीन, बजेट, उद्योग) अधिक विस्तारात सांगा."
            elif language == "hindi":
                return "खेद है! आपके प्रश्न से संबंधित कोई योजना नहीं मिली। कृपया अपने विवरण (भूमि, बजट, उद्यम) विस्तार से बताएं।"
            else:
                return "No matching schemes found for your query. Please provide more details (land size, budget, enterprise type)."

        # Format header
        if language == "marathi":
            header = f"तुमच्यासाठी {len(results)} योजना प्रासंगिक दिसतात:\n\n"
        elif language == "hindi":
            header = f"आपके लिए {len(results)} योजनाएं प्रासंगिक लग रही हैं:\n\n"
        else:
            header = f"I found {len(results)} relevant schemes for you:\n\n"

        # Format each result
        formatted = [header]
        for idx, result in enumerate(results, 1):
            scheme = result.scheme
            name = scheme.get("name", "")
            summary = scheme.get("summary", "")
            source_url = scheme.get("source_url", "")
            source_name = scheme.get("source_name", "")

            if language == "marathi":
                entry = f"{idx}. {name}\n   {summary}\n   अधिकृत माहिती: {source_name}\n   URL: {source_url}\n"
            elif language == "hindi":
                entry = f"{idx}. {name}\n   {summary}\n   अधिकारी जानकारी: {source_name}\n   URL: {source_url}\n"
            else:
                entry = f"{idx}. {name}\n   {summary}\n   Official source: {source_name}\n   URL: {source_url}\n"

            formatted.append(entry)

        # Add disclaimer
        if language == "marathi":
            disclaimer = "\n⚠️ महत्वाचे: तुमची योग्यता अधिकृत पोर्टलवर तपासा. आम्ही कधीही अनुदान, मुदती किंवा आवश्यक कागदपत्रे बनवत नाही."
        elif language == "hindi":
            disclaimer = "\n⚠️ महत्वपूर्ण: आधिकारिक पोर्टल पर अपनी पात्रता सत्यापित करें। हम कभी भी सब्सिडी, समय सीमा या आवश्यक दस्तावेज़ नहीं बनाते।"
        else:
            disclaimer = "\n⚠️ Important: Please verify your eligibility on the official portal. We never invent subsidy amounts, deadlines, or required documents."

        formatted.append(disclaimer)
        return "\n".join(formatted)

    @classmethod
    def get_all_schemes(cls) -> List[Dict[str, Any]]:
        """Get all schemes (useful for admin/debug)"""
        return cls._load_schemes()

    @classmethod
    def get_scheme_count(cls) -> int:
        """Get total number of schemes in dataset"""
        return len(cls._load_schemes())

    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all unique scheme categories"""
        schemes = cls._load_schemes()
        categories = set()
        for scheme in schemes:
            cat = scheme.get("category")
            if cat:
                categories.add(cat)
        return sorted(list(categories))

    @classmethod
    def get_scopes(cls) -> List[str]:
        """Get all unique scheme scopes (central, maharashtra, etc.)"""
        schemes = cls._load_schemes()
        scopes = set()
        for scheme in schemes:
            scope = scheme.get("scope")
            if scope:
                scopes.add(scope)
        return sorted(list(scopes))
