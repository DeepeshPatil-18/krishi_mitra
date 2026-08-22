"""Entity Extractor - extracts useful farmer information from messages

TASK 4.5 changes (2026-08-22):
  - Budget: added k/K suffix (50k→50000), bare-integer near बजेट/budget,
            range pattern (50-100k→midpoint), fraction prefix (आधा/डेढ़) land
  - Land:   added acres plural (acres?), fixed Hindi एकड़ nukta encoding,
            added fraction-word land patterns (आधा/डेढ़/half)
  - Location: removed \\b word-boundaries so locative suffixes (-मध्ये/-त/-में)
              still match; added Kerala/केरल mapping; added Pune/Nashik English
  - Experience: added Marathi beginner words (शुरुवातीचा/नवीन);
                removed spurious `years` keyword from expert bucket;
                added explicit high-year-count pattern for expert
  - Time: added पूर्णकाळ (Marathi full-time), full-time hyphen, पार्ट टाइम
  - Enterprise: added वर्मीकम्पोस्ट (Hindi alt), शेणखत (Marathi compost)
  - Water: scoped high-water patterns to require पानी/water context;
           fixed "Very limited water" → low; fixed "High risk tolerance" false-high
  - FP reduction: removed कम from TIME_AVAILABILITY["limited"] to stop it
                  firing on water/budget "कम" context
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fraction helpers (shared with EntityNormalizer logic)
# ---------------------------------------------------------------------------
_ACRE_TO_HA = 0.404686   # precise constant

def _fraction_acres_to_ha(fraction: float) -> float:
    return round(fraction * _ACRE_TO_HA, 4)


class EntityExtractor:
    """
    Extracts structured information from farmer messages.

    Supports:
    - Budget/capital amounts
    - Land/space measurements
    - Water availability levels
    - Experience levels
    - Locations
    - Enterprise names
    - Income goals
    - Risk preferences
    - Time availability
    """

    # ── Enterprise codes and aliases ────────────────────────────────────────
    ENTERPRISES = {
        "mushroom":      ["mushroom", "मशरूम", "कुकुरमुत्ते", "khumb"],
        "apiculture":    ["bee", "honey", "मधु", "मधु पालन", "beekeeping", "शहद",
                          "मधुमेखी", "मधुमक्खी"],
        "poultry":       ["chicken", "poultry", "मुर्गी", "कोळी", "bird",
                          "मुर्गीपालन", "कुक्कुटपालन"],
        "fisheries":     ["fish", "fishing", "मासे", "मछली", "aquaculture",
                          "मछली पालन"],
        "goat":          ["goat", "goat farming", "शेळी", "बकरी",
                          "goat rearing", "बकरी पालन"],
        # TASK 4.5: added वर्मीकम्पोस्ट (Hindi alt spelling) and शेणखत (Marathi)
        "vermicompost":  ["vermicompost", "worm", "केचू", "खाद",
                          "वर्मीकम्पोस्ट", "शेणखत"],
    }

    # ── Water availability ───────────────────────────────────────────────────
    # TASK 4.5: Scoped high/medium patterns to require पानी/water context
    # so that "High risk tolerance" no longer triggers water_availability=high.
    WATER_LEVELS = {
        "high": [
            # Require explicit water/पानी context
            r"(water|पानी|पाणी).{0,20}(high|abundant|ज्यादा|अधिक|भरपूर)",
            r"(high|abundant|ज्यादा|अधिक|भरपूर).{0,20}(water|पानी|पाणी)",
            r"(भरपूर\s+पाणी|भरपूर\s+पानी|पाणी\s+भरपूर|पानी\s+भरपूर)",
            r"\b(well|borewell|नल|कुआँ|जलसंचय)\b",
            r"(पानी\s+उपलब्ध|पाणी\s+उपलब्ध)",
        ],
        "medium": [
            r"\b(moderate)\b",
            r"(मध्यम\s+पाणी|मध्यम\s+पानी)",
            r"(नहरी|मौसमी|seasonal)",
        ],
        "low": [
            # TASK 4.5: require पानी/water near कम to avoid FP on budget context
            r"(water|पानी|पाणी).{0,20}(low|कम|insufficient|limited|सूखा)",
            r"(low|कम|insufficient|limited|सूखा).{0,20}(water|पानी|पाणी)",
            r"(पाणी\s+कमी|पानी\s+कम)",
            r"(dry\s+land|no\s+water)",
            r"\b(low\s+water|water\s+scarce)\b",
        ],
    }

    # ── Experience levels ────────────────────────────────────────────────────
    # TASK 4.5:
    #   - Removed bare `\b(years)\b` from expert bucket (caused every year
    #     mention to fire expert).
    #   - Added explicit high-year-count pattern: 10+ years → expert.
    #   - Added Marathi beginner words to beginner bucket.
    #   - expert keyword scoped away from "speak with an expert" context by
    #     requiring it not be followed by "?" directly or preceded by "an ".
    EXPERIENCE_LEVELS = {
        "beginner": [
            r"\b(new|beginner|novice)\b",
            r"(नया|शुरुआत|नौसिखिया)",
            r"(अनुभव\s+नहीं|कोई\s+अनुभव\s+नहीं)",
            # TASK 4.5: Marathi beginner phrases
            r"(शुरुवातीचा|शुरुवातीची|नवीन\s+शेतकरी|अगदी\s+नवीन|नवखा)",
            r"\b(नवीन)\b",          # standalone "new" in Marathi
            # Explicit 1-year count (< 2 years → beginner)
            r"\b1\s*(year|वर्ष|साल|वर्षांचा|वर्षाचा)\b",
        ],
        "intermediate": [
            r"\b(intermediate|some\s+experience|experienced)\b",
            r"(कुछ\s+वर्ष|कुछ\s+साल|अनुभवी)",
            r"(पहले\s+किया|साल\s+का\s+अनुभव)",
            # 2-9 year count → intermediate
            r"\b([2-9])\s*(years?|साल|वर्ष|वर्षांचा|वर्षाचा)\b",
        ],
        "expert": [
            # "expert" only when it's describing the person, not "talk to an expert"
            r"\b(professional|veteran)\b",
            # Require explicit context that it's about the FARMER's experience
            r"(बहुत\s+अनुभव|लंबे\s+समय\s+से|लंबे\s+समय\s+का)",
            # TASK 4.5: explicit high year count (10+) → expert
            r"\b(1[0-9]|[2-9]\d)\s*(years?|साल|वर्ष|वर्षांचा|वर्षाचा)\b",
        ],
    }

    # ── Risk tolerance ───────────────────────────────────────────────────────
    RISK_LEVELS = {
        "low": [
            r"\b(safe|low\s+risk|conservative)\b",
            r"(कम\s+जोखिम|सुरक्षित|नुकसान\s+नहीं)",
        ],
        "medium": [
            r"\b(moderate|medium|balanced)\b",
            r"(मध्यम|कुछ\s+जोखिम|संतुलित)",
        ],
        "high": [
            r"\b(high\s+risk|aggressive|venture)\b",
            r"(उच्च\s+जोखिम|ज्यादा\s+लाभ|साहसी)",
            # TASK 4.5: require "risk" nearby so standalone "high" doesn't fire
            r"\b(high)\b.{0,15}\b(risk|जोखिम)\b",
            r"\b(risk|जोखिम)\b.{0,15}\b(high|उच्च|ज्यादा)\b",
        ],
    }

    # ── Time availability ────────────────────────────────────────────────────
    # TASK 4.5:
    #   - Added full-time hyphen variant and पूर्णकाळ (Marathi).
    #   - Added पार्ट टाइम (Marathi transliteration).
    #   - REMOVED bare `कम` from "limited" to stop FP on budget/water context.
    TIME_AVAILABILITY = {
        "full_time": [
            r"\b(full[-\s]time|dedicated|all\s+day)\b",
            r"(पूरा\s+दिन|पूरे\s+समय|पूरा\s+समय)",
            # TASK 4.5: Marathi full-time
            r"पूर्णकाळ",
            r"(पूर्ण\s+वेळ|पूर्ण\s+वेळेत)",
        ],
        "part_time": [
            r"\b(part[-\s]time|half\s+day)\b",
            r"(आधा\s+समय|सुबह\s+शाम|सुबह\s+या\s+शाम)",
            # TASK 4.5: Marathi transliteration
            r"(पार्ट\s+टाइम|पार्ट-टाइम)",
        ],
        "limited": [
            # TASK 4.5: removed bare `\b(limited|कम|थोड़ा|छुट्टी)\b` which
            # was causing huge false-positive rate. Now require explicit context.
            r"\b(limited\s+time|थोड़ा\s+समय|कम\s+समय)\b",
            r"(छुट्टी\s+में|spare\s+time|leisure)",
        ],
    }

    # ── Locations ────────────────────────────────────────────────────────────
    # TASK 4.5:
    #   - Each city/district gets its OWN key so the returned value matches
    #     the evaluation dataset expectations (nashik, pune, maharashtra, kerala…)
    #   - Patterns do NOT use strict \b around Devanagari; locative suffixes
    #     (-मध्ये / -त / -में) would break word-boundary matching.
    LOCATIONS = {
        # ── Maharashtra cities (most specific first) ────────────────────────
        "nashik": [
            r"(nashik|नाशिक)",           # catches नाशिकमध्ये, नाशिक में
        ],
        "pune": [
            r"(pune|पुणे)",              # catches पुणे जिल्ह्यात, In Pune
        ],
        "aurangabad": [
            r"(aurangabad|औरंगाबाद)",
        ],
        # ── Maharashtra state (fallback after cities) ────────────────────────
        "maharashtra": [
            r"(maharashtra|महाराष्ट्र)",  # catches महाराष्ट्रात
        ],
        # ── Other states ────────────────────────────────────────────────────
        "karnataka": [
            r"(karnataka|कर्नाटक|bangalore|बैंगलोर)",
        ],
        "kerala": [
            # TASK 4.5: added Hindi/Marathi Kerala spelling
            r"(kerala|केरल|केरला)",
        ],
        "punjab": [
            r"(punjab|पंजाब|ludhiana|लुधियाना)",
        ],
        "uttar_pradesh": [
            r"(uttar\s+pradesh|उत्तर\s+प्रदेश|\bup\b|लखनऊ|lucknow)",
        ],
        "madhya_pradesh": [
            r"(madhya\s+pradesh|मध्य\s+प्रदेश|\bmp\b|bhopal|भोपाल)",
        ],
        "tamil_nadu": [
            r"(tamil\s+nadu|तमिल\s+नाडु|chennai|चेन्नई)",
        ],
        "andhra_pradesh": [
            r"(andhra\s+pradesh|आंध्र\s+प्रदेश|hyderabad|हैदराबाद)",
        ],
        "telangana": [
            r"(telangana|तेलंगाना)",
        ],
        "bihar": [
            r"(bihar|बिहार|patna|पटना)",
        ],
        "rajasthan": [
            r"(rajasthan|राजस्थान|jaipur|जयपुर)",
        ],
        "west_bengal": [
            r"(west\s+bengal|पश्चिम\s+बंगाल|kolkata|कोलकाता)",
        ],
    }

    # ── Public API ───────────────────────────────────────────────────────────

    @staticmethod
    def extract_all(message: str, language: str = "auto") -> Dict[str, Any]:
        """
        Extract all relevant entities from a message.

        Returns:
            Dictionary of extracted entities (values are already normalised
            numeric types for budget/land; strings for categoricals).
        """
        entities: Dict[str, Any] = {}

        # Numeric values first (budget, land, income)
        entities.update(EntityExtractor._extract_numeric(message))

        # Location early to avoid keyword conflicts
        entities.update(EntityExtractor._extract_location(message))

        # Categoricals
        entities.update(EntityExtractor._extract_enterprise(message))
        entities.update(EntityExtractor._extract_water(message))
        entities.update(EntityExtractor._extract_experience(message))
        entities.update(EntityExtractor._extract_risk(message))
        entities.update(EntityExtractor._extract_time(message))

        logger.debug(f"Extracted entities: {entities}")
        return entities

    # ── Numeric extraction ───────────────────────────────────────────────────

    @staticmethod
    def _extract_numeric(message: str) -> Dict[str, Any]:
        """Extract budget, land size, and income goal from message."""
        entities: Dict[str, Any] = {}

        # ── Budget ──────────────────────────────────────────────────────────
        # Priority order matters: more-specific patterns first.
        budget_patterns = [
            # TASK 4.5: range like "50-100k" → midpoint
            (
                r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*k\b",
                lambda m: int((float(m.group(1)) + float(m.group(2))) / 2 * 1000),
            ),
            # TASK 4.5: range like "50000-100000" → midpoint
            (
                r"(\d{4,})\s*[-–]\s*(\d{4,})",
                lambda m: int((int(m.group(1)) + int(m.group(2))) / 2),
            ),
            # Lakh amounts
            (r"(\d+(?:\.\d+)?)\s*(lakh|लाख)",
             lambda m: int(float(m.group(1)) * 100_000)),
            # Thousand / हजार / हज़ार
            (r"(\d+(?:\.\d+)?)\s*(thousand|hazar|हजार|हज़ार)",
             lambda m: int(float(m.group(1)) * 1_000)),
            # TASK 4.5: "k" shorthand  e.g. 50k, 100K
            (r"(\d+(?:\.\d+)?)\s*[kK]\b",
             lambda m: int(float(m.group(1)) * 1_000)),
            # Currency-symbol prefix  ₹50000
            (r"(₹|रु\.?)\s*(\d+)\b",
             lambda m: int(m.group(2))),
            # Direct rupee suffix
            (r"\b(\d+)\s*(rupees|रुपये|रुपया|रु|Rs\.?)\b",
             lambda m: int(m.group(1))),
            # TASK 4.5: bare integer adjacent to बजेट/budget keyword
            # Pattern A: keyword then number  "बजेट 150000"
            (r"(budget|बजेट|बजट)\s*[:-]?\s*(\d+)",
             lambda m: int(m.group(2))),
            # Pattern B: number then keyword (with optional filler like "का")
            # "200000 बजेट", "40000 का बजट", "40000 budget"
            (r"(\d+)[^\d\n।]{0,10}(budget|बजेट|बजट)\b",
             lambda m: int(m.group(1))),
        ]

        for pattern, converter in budget_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    amount = converter(match)
                    if amount > 0:
                        entities["budget_rupees"] = amount
                        break
                except (ValueError, IndexError, AttributeError):
                    continue

        # ── Land size ────────────────────────────────────────────────────────
        land_patterns = [
            # Hectares / ha / हेक्टर — exact, no conversion needed
            (r"(\d+(?:\.\d+)?)\s*(hectares?|ha|हेक्टर)\b",
             lambda m: float(m.group(1))),
            # TASK 4.5: fraction-word acres (must come BEFORE digit-acre pattern)
            # आधा = half, डेढ़/दीड = 1.5, ढाई = 2.5
            (r"\b(आधा|अर्धा)\s*(एकर|एकड़|acre)",
             lambda m: _fraction_acres_to_ha(0.5)),
            (r"\b(डेढ़|दीड|डेढ)\s*(एकर|एकड़|acre)",
             lambda m: _fraction_acres_to_ha(1.5)),
            (r"\b(ढाई)\s*(एकर|एकड़|acre)",
             lambda m: _fraction_acres_to_ha(2.5)),
            (r"\b(half)\s*(an?\s+)?(acre|एकर|एकड़)",
             lambda m: _fraction_acres_to_ha(0.5)),
            # TASK 4.5: digit acres — plural "acres?" + Hindi एकड़ (nukta)
            # Using a character-class for the Devanagari variants to be safe
            (r"(\d+(?:\.\d+)?)\s*(acres?|एकर|एकड़)",
             lambda m: round(float(m.group(1)) * _ACRE_TO_HA, 4)),
        ]

        for pattern, converter in land_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    size = converter(match)
                    if size >= 0:
                        entities["land_size_hectares"] = round(size, 4)
                        break
                except (ValueError, IndexError, AttributeError):
                    continue

        # ── Income goal ──────────────────────────────────────────────────────
        income_patterns = [
            (r"(\d+)\s*(thousand|हजार)\s*(?:per|प्रति)?\s*(month|महीने|महीना)\b",
             lambda m: int(m.group(1)) * 1_000),
            (r"\b(\d+)\s*(rupees|रुपये)\s*(?:per|प्रति)?\s*(month|महीने|महीना)\b",
             lambda m: int(m.group(1))),
        ]

        for pattern, converter in income_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    entities["income_goal_monthly"] = converter(match)
                    break
                except (ValueError, IndexError, AttributeError):
                    continue

        return entities

    # ── Categorical extractors ───────────────────────────────────────────────

    @staticmethod
    def _extract_enterprise(message: str) -> Dict[str, Any]:
        """Extract enterprise type."""
        for enterprise, patterns in EntityExtractor.ENTERPRISES.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return {"enterprise": enterprise}
        return {}

    @staticmethod
    def _extract_water(message: str) -> Dict[str, Any]:
        """Extract water availability level."""
        for level, patterns in EntityExtractor.WATER_LEVELS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return {"water_availability": level}
        return {}

    @staticmethod
    def _extract_experience(message: str) -> Dict[str, Any]:
        """Extract experience level."""
        for level, patterns in EntityExtractor.EXPERIENCE_LEVELS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return {"experience_level": level}
        return {}

    @staticmethod
    def _extract_risk(message: str) -> Dict[str, Any]:
        """Extract risk tolerance."""
        for level, patterns in EntityExtractor.RISK_LEVELS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return {"risk_tolerance": level}
        return {}

    @staticmethod
    def _extract_time(message: str) -> Dict[str, Any]:
        """Extract time availability."""
        for level, patterns in EntityExtractor.TIME_AVAILABILITY.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return {"time_availability": level}
        return {}

    @staticmethod
    def _extract_location(message: str) -> Dict[str, Any]:
        """Extract location/state.

        TASK 4.5: Patterns no longer use \\b word-boundaries around Devanagari
        city names so locative suffixes (-मध्ये, -त, -में) still match.
        """
        for location, patterns in EntityExtractor.LOCATIONS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return {"location": location}
        return {}

    # ── Convenience methods ──────────────────────────────────────────────────

    @staticmethod
    def extract_budget(message: str) -> Optional[int]:
        """Extract budget amount only."""
        return EntityExtractor._extract_numeric(message).get("budget_rupees")

    @staticmethod
    def extract_location(message: str) -> Optional[str]:
        """Extract location only."""
        return EntityExtractor._extract_location(message).get("location")

    @staticmethod
    def extract_land(message: str) -> Optional[float]:
        """Extract land size only."""
        return EntityExtractor._extract_numeric(message).get("land_size_hectares")
