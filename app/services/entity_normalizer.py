"""
Entity Normalizer - deterministic normalization of extracted entity values

Converts raw extracted values to standardized, normalized forms.
Preserves both raw and normalized values for transparency.
Does NOT guess when ambiguous - marks as uncertain instead.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class EntityNormalizer:
    """Deterministic entity value normalization without ML"""
    
    # Marathi number words
    MARATHI_NUMBERS = {
        'शून्य': 0, 'एक': 1, 'दोन': 2, 'तीन': 3, 'चार': 4, 'पाच': 5,
        'सहा': 6, 'सात': 7, 'आठ': 8, 'नऊ': 9, 'दहा': 10,
        'अकरा': 11, 'बारा': 12, 'तेरा': 13, 'चौदा': 14, 'पंधरा': 15,
        'सोळा': 16, 'सतरा': 17, 'अठरा': 18, 'एकोणीस': 19, 'वीस': 20,
        'तीस': 30, 'चाळीस': 40, 'पन्नास': 50, 'साठ': 60, 'सत्तर': 70,
        'ऐंशी': 80, 'नव्वद': 90, 'शंभर': 100, 'हजार': 1000, 'लाख': 100000
    }
    
    # Hindi number words
    HINDI_NUMBERS = {
        'शून्य': 0, 'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पाँच': 5,
        'छः': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
        'ग्यारह': 11, 'बारह': 12, 'तेरह': 13, 'चौदह': 14, 'पंद्रह': 15,
        'सोलह': 16, 'सत्रह': 17, 'अठारह': 18, 'उन्नीस': 19, 'बीस': 20,
        'तीस': 30, 'चालीस': 40, 'पचास': 50, 'साठ': 60, 'सत्तर': 70,
        'अस्सी': 80, 'नब्बे': 90, 'सौ': 100, 'हज़ार': 1000, 'लाख': 100000
    }
    
    # Devanagari digits
    DEVANAGARI_DIGITS = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }
    
    # Location districts (Marathi/Hindi names to canonical form)
    DISTRICTS = {
        # Maharashtra
        'नाशिक': 'nashik', 'नासिक': 'nashik', 'nasik': 'nashik', 'nashik': 'nashik',
        'पुणे': 'pune', 'पुणेत': 'pune', 'pune': 'pune',
        'औरंगाबाद': 'aurangabad', 'aurangabad': 'aurangabad',
        'अमरावती': 'amravati', 'amravati': 'amravati',
        'अकोला': 'akola', 'akola': 'akola',
        'बिड': 'bid', 'बीड': 'bid', 'bid': 'bid',
        'बुलढाणा': 'buldhana', 'buldhana': 'buldhana',
        'चंद्रपुर': 'chandrapur', 'chandrapur': 'chandrapur',
        'धुळे': 'dhule', 'धूले': 'dhule', 'dhule': 'dhule',
        'गढ़चिरोली': 'gadchiroli', 'gadchiroli': 'gadchiroli',
        'गोवा': 'goa', 'goa': 'goa',
        'हिंगोली': 'hingoli', 'hingoli': 'hingoli',
        'जालना': 'jalna', 'jalna': 'jalna',
        'जत': 'jat', 'jat': 'jat',
        'कोल्हापुर': 'kolhapur', 'kolhapur': 'kolhapur',
        'लातूर': 'latur', 'latur': 'latur',
        'मोंघे': 'monghe', 'monghe': 'monghe',
        'नागपुर': 'nagpur', 'nagpur': 'nagpur',
        'उस्मानाबाद': 'usmanabad', 'usmanabad': 'usmanabad',
        'परभणी': 'parbhani', 'parbhani': 'parbhani',
        'रत्नागिरी': 'ratnagiri', 'ratnagiri': 'ratnagiri',
        'सांगली': 'sangli', 'sangli': 'sangli',
        'सातारा': 'satara', 'satara': 'satara',
        'सिंधुदुर्ग': 'sindhudurg', 'sindhudurg': 'sindhudurg',
        'सोलापुर': 'solapur', 'solapur': 'solapur',
        'ठाणे': 'thane', 'thane': 'thane',
        'वर्धा': 'wardha', 'wardha': 'wardha',
        'वाशिम': 'washim', 'washim': 'washim',
        'यवतमाल': 'yavatmal', 'yavatmal': 'yavatmal',
        # Abbreviated forms
        'बेलगाव': 'belgaum', 'belgaum': 'belgaum',
        'बेळगाव': 'belgaum',
    }
    
    # Time units
    TIME_UNITS = {
        'दिन': 'days', 'din': 'days', 'day': 'days', 'days': 'days',
        'सप्ताह': 'weeks', 'week': 'weeks', 'weeks': 'weeks',
        'महीना': 'months', 'महिना': 'months', 'month': 'months', 'months': 'months',
        'महीने': 'months', 'माह': 'months',
        'साल': 'years', 'year': 'years', 'years': 'years',
        'वर्ष': 'years', 'वर्ष': 'years'
    }
    
    # Experience level mappings
    EXPERIENCE_KEYWORDS = {
        'beginner': ['नया', 'शुरुवातीचा', 'नौसिखिया', 'novice', 'beginner', 'new', 'नया किसान'],
        'intermediate': ['मध्यवर्ती', 'कुछ', 'some', 'experienced', 'साल का अनुभव'],
        'expert': ['विशेषज्ञ', 'expert', 'professional', 'veteran', 'बहुत अनुभव', 'many years']
    }
    
    # Risk tolerance mappings
    RISK_KEYWORDS = {
        'low': ['कम', 'जोखीम', 'safe', 'low', 'conservative', 'सुरक्षित', 'कम जोखिम'],
        'medium': ['मध्यम', 'medium', 'balanced', 'moderate', 'संतुलित'],
        'high': ['उच्च', 'high', 'risk', 'aggressive', 'venture', 'साहसी', 'उच्च जोखिम']
    }
    
    # Time availability mappings
    TIME_AVAILABILITY_KEYWORDS = {
        'full_time': ['पूरा', 'पूरे दिन', 'full', 'dedicated', 'पूरे समय'],
        'part_time': ['आधा', 'part', 'half', 'आधा समय'],
        'limited': ['कम', 'limited', 'थोड़ा', 'छुट्टी']
    }
    
    @staticmethod
    def normalize_number(raw_value: str) -> Optional[Tuple[float, str]]:
        """
        Normalize Marathi/Hindi/Devanagari numbers to float
        
        Args:
            raw_value: Raw string like "पन्नास हजार" or "५०" or "50000" or "50-100k"
            
        Returns:
            Tuple of (normalized_value, format_type) or None if cannot normalize
        """
        if not raw_value or not isinstance(raw_value, str):
            return None
        
        raw_value = raw_value.strip()
        
        # Try 0: Check for ranges/approximations first
        range_result = EntityNormalizer._parse_budget_range(raw_value)
        if range_result:
            return (range_result, 'range_or_approximation')
        
        # Try 0.5: Mixed Arabic numerals with number words (e.g., "50 हजार")
        mixed_result = EntityNormalizer._parse_mixed_numbers(raw_value)
        if mixed_result:
            return (mixed_result, 'mixed_arabic_words')
        
        # Try 1: Direct Arabic numeral
        try:
            # Remove commas first
            cleaned = raw_value.replace(',', '').replace(' ', '')
            # Convert Devanagari to Arabic
            for dev_digit, arab_digit in EntityNormalizer.DEVANAGARI_DIGITS.items():
                cleaned = cleaned.replace(dev_digit, arab_digit)
            value = float(cleaned)
            return (value, 'arabic_numeral')
        except ValueError:
            pass
        
        # Try 2: Marathi number words
        normalized = EntityNormalizer._parse_number_words(raw_value, EntityNormalizer.MARATHI_NUMBERS)
        if normalized:
            return (normalized, 'marathi_words')
        
        # Try 3: Hindi number words
        normalized = EntityNormalizer._parse_number_words(raw_value, EntityNormalizer.HINDI_NUMBERS)
        if normalized:
            return (normalized, 'hindi_words')
        
        # Could not normalize
        return None
    
    @staticmethod
    def _parse_number_words(text: str, number_dict: Dict[str, int]) -> Optional[float]:
        """Parse number words like 'पन्नास हजार' to 50000
        
        Handles patterns like:
        - "पन्नास हजार" → 50 * 1000 = 50000
        - "2 हजार" → 2 * 1000 = 2000
        - "पन्नास" → 50
        """
        text_lower = text.lower()
        
        # Find all number words in order of appearance
        found_words = []
        for word in number_dict.keys():
            if word.lower() in text_lower:
                pos = text_lower.find(word.lower())
                found_words.append((pos, word.lower(), number_dict[word]))
        
        if not found_words:
            return None
        
        # Sort by position
        found_words.sort(key=lambda x: x[0])
        
        # Build value: multiplier + additive structure
        # "पन्नास हजार" = 50 (पन्नास) * 1000 (हजार) = 50000
        # "2 लाख 50 हजार" = 2*100000 + 50*1000 = 250000
        # "2 हजार" = 2 * 1000 = 2000
        
        total = 0
        current_number = 0
        
        for _, word, value in found_words:
            if value >= 100000:  # lakh, crore (multiplier for millions+)
                if current_number > 0:
                    total += current_number * value
                    current_number = 0
                else:
                    total += value
            elif value >= 1000:  # thousand (multiplier for thousands)
                if current_number > 0:
                    total += current_number * value
                    current_number = 0
                else:
                    total += value
            elif value >= 100:  # hundred (multiplier for hundreds)
                if current_number > 0:
                    total += current_number * value
                    current_number = 0
                else:
                    total += value
            else:  # ones, tens (0-99)
                current_number = value
        
        # Add any remaining number (if it wasn't multiplied)
        if current_number > 0:
            total += current_number
        
        return float(total) if total > 0 else None
    
    @staticmethod
    def _parse_budget_range(text: str) -> Optional[float]:
        """
        Parse budget ranges and approximations to single value (midpoint)
        
        Handles patterns like:
        - "50000 to 100000" → 75000
        - "50-100k" → 75000
        - "around 50000" → 50000
        - "लगभग 50000" → 50000
        
        Returns:
            Midpoint of range or the single value if approximation
        """
        text_lower = text.lower()
        
        # Check for approximation markers (use the number as-is)
        approximation_markers = ['around', 'लगभग', 'करीब', 'approximately', 'approx', 'about', 'छोटे मोटे']
        for marker in approximation_markers:
            if marker in text_lower or marker in text:
                # Just remove marker and try to parse the remaining number
                cleaned = text.lower().replace(marker, '').strip()
                return EntityNormalizer.normalize_number(cleaned)[0] if EntityNormalizer.normalize_number(cleaned) else None
        
        # Check for range patterns: "X to Y", "X-Y", "X से Y"
        range_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:to|से|-)\s*(\d+(?:\.\d+)?)',  # English/Hindi
            r'([०-९]+(?:\.[०-९]+)?)\s*(?:to|से|-)\s*([०-९]+(?:\.[०-९]+)?)',  # Devanagari
        ]
        
        for pattern in range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Convert Devanagari to Arabic if needed
                    start_str = match.group(1)
                    end_str = match.group(2)
                    for dev, arab in EntityNormalizer.DEVANAGARI_DIGITS.items():
                        start_str = start_str.replace(dev, arab)
                        end_str = end_str.replace(dev, arab)
                    
                    start_val = float(start_str)
                    end_val = float(end_str)
                    
                    # Handle "k" suffix (thousands)
                    if 'k' in text_lower or 'K' in text:
                        if start_val < 1000:  # Assume "k" means thousands
                            start_val *= 1000
                        if end_val < 1000:
                            end_val *= 1000
                    
                    # Return midpoint
                    return (start_val + end_val) / 2.0
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @staticmethod
    def _parse_mixed_numbers(text: str) -> Optional[float]:
        """
        Parse mixed Arabic numerals with number words (e.g., "50 हजार", "2 लाख")
        
        Args:
            text: String like "50 हजार" or "2 लाख"
            
        Returns:
            Normalized value or None
        """
        # Pattern: Arabic digit followed by space and number word
        pattern = r'(\d+(?:\.\d+)?)\s*(हजार|हज़ार|लाख|करोड़|crore|lakh|thousand|hundred)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                digit_value = float(match.group(1))
                word = match.group(2).lower()
                
                # Map word to multiplier
                if word in ['हजार', 'हज़ार', 'thousand']:
                    return digit_value * 1000
                elif word in ['लाख', 'lakh']:
                    return digit_value * 100000
                elif word in ['करोड़', 'crore']:
                    return digit_value * 10000000
                elif word in ['hundred']:
                    return digit_value * 100
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def normalize_land_size(raw_value: str) -> Optional[Tuple[float, str]]:
        """
        Normalize land sizes to hectares
        
        Args:
            raw_value: Like "2 एकर" or "1 hectare" or "आधा एकर" or "1.5 hectares"
            
        Returns:
            Tuple of (hectares, unit_type) or None
        """
        if not raw_value:
            return None
        
        raw_value_lower = raw_value.lower().strip()
        
        # Extract numeric part first - try multiple patterns
        numeric_part = None
        numeric_str = None
        
        # Try Devanagari digits with optional decimal
        pattern_devanagari = r'([०-९]+(?:\.[०-९]+)?)'
        match = re.search(pattern_devanagari, raw_value)
        if match:
            numeric_str = match.group(1)
            # Convert Devanagari to Arabic
            for dev, arab in EntityNormalizer.DEVANAGARI_DIGITS.items():
                numeric_str = numeric_str.replace(dev, arab)
            try:
                numeric_part = float(numeric_str)
            except ValueError:
                numeric_part = None
        
        # If not found, try Arabic digits
        if numeric_part is None:
            pattern_arabic = r'(\d+(?:\.\d+)?)'
            match = re.search(pattern_arabic, raw_value)
            if match:
                numeric_str = match.group(1)
                try:
                    numeric_part = float(numeric_str)
                except ValueError:
                    numeric_part = None
        
        # Handle fraction words - if no numeric part found, check for fraction words
        # "आधा एकर" = 0.5 acre, "डेढ़ एकर" = 1.5 acres
        if numeric_part is None:
            if 'आधा' in raw_value or 'आध' in raw_value:
                numeric_part = 0.5
            elif 'डेढ' in raw_value or 'डेढ़' in raw_value:
                numeric_part = 1.5
            elif 'साडे' in raw_value or 'सेडे' in raw_value:
                # "साडे" typically means +0.5
                numeric_part = 1.5  # Default if used without number
            else:
                return None  # No numeric value found
        else:
            # Numeric part found - apply fraction modifiers
            if 'आधा' in raw_value or 'आध' in raw_value or 'आधी' in raw_value:
                numeric_part = numeric_part / 2.0
            elif 'साडे' in raw_value or 'सेडे' in raw_value:
                # "साडे" typically means +0.5 in Marathi (e.g., साडे दोन = 2.5)
                numeric_part = numeric_part + 0.5
            elif 'डेढ' in raw_value or 'डेढ़' in raw_value:
                # "डेढ़" means 1.5 (multiplier applied to preceding number)
                numeric_part = numeric_part * 1.5
        
        if numeric_part is None or numeric_part <= 0:
            return None
        
        # Determine source unit and convert to hectares
        # Critical: Check both 'hectare' AND 'हेक्टेयर' variants
        if ('hectare' in raw_value_lower or 'ha' in raw_value_lower or 
            'हेक्टेयर' in raw_value or 'हेक्टर' in raw_value):
            # Already in hectares
            return (numeric_part, 'hectare')
        elif ('एकर' in raw_value or 'एकड़' in raw_value or 
              'acre' in raw_value_lower or 'ares' in raw_value_lower):
            # 1 acre = 0.404686 hectares (using precise conversion)
            hectares = numeric_part * 0.404686
            return (hectares, 'acre')
        elif 'bigha' in raw_value_lower or 'बीघा' in raw_value or 'बिघा' in raw_value:
            # 1 bigha ≈ 0.67 hectares (varies by region, using standard)
            hectares = numeric_part * 0.67
            return (hectares, 'bigha')
        elif 'guntha' in raw_value_lower or 'गुंठा' in raw_value or 'गुंथा' in raw_value:
            # 1 guntha = 0.0101 hectares (40 guntha ≈ 1 acre)
            hectares = numeric_part * 0.0101
            return (hectares, 'guntha')
        
        # Could not determine unit - return None (do not guess)
        return None
    
    @staticmethod
    def normalize_location(raw_value: str) -> Optional[Tuple[str, str]]:
        """
        Normalize location to district (not state)
        
        Args:
            raw_value: Like "नाशिकमध्ये" or "Nashik"
            
        Returns:
            Tuple of (district_code, format_type) or None
        """
        if not raw_value:
            return None
        
        raw_value = raw_value.strip()
        
        # Remove postpositions: मध्ये, में, मध्य, etc
        clean_value = re.sub(r'(मध्ये|मध्य|में|जिल्ह्यात|जिला|जिले|district|District)$', '', raw_value).strip()
        
        # Try exact match first
        if clean_value in EntityNormalizer.DISTRICTS:
            return (EntityNormalizer.DISTRICTS[clean_value], 'exact_match')
        
        # Try case-insensitive
        clean_lower = clean_value.lower()
        for key, value in EntityNormalizer.DISTRICTS.items():
            if key.lower() == clean_lower:
                return (value, 'case_insensitive')
        
        # Try partial match (prefix)
        for key, value in EntityNormalizer.DISTRICTS.items():
            if key.lower().startswith(clean_lower) or clean_lower.startswith(key.lower()):
                return (value, 'partial_match')
        
        # Could not normalize - return None (do not guess)
        return None
    
    @staticmethod
    def normalize_time_numeric(raw_value: str) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        Normalize time expressions with numeric values
        
        Args:
            raw_value: Like "3 महीने" or "6 months"
            
        Returns:
            Tuple of ({"value": int, "unit": str}, format_type) or None
        """
        if not raw_value:
            return None
        
        # Extract number
        numeric_match = re.search(r'(\d+)', raw_value)
        if not numeric_match:
            return None
        
        value = int(numeric_match.group(1))
        
        # Find unit
        for unit_word, unit_type in EntityNormalizer.TIME_UNITS.items():
            if unit_word.lower() in raw_value.lower():
                return ({"value": value, "unit": unit_type}, 'numeric_with_unit')
        
        # Could not determine unit
        return None
    
    @staticmethod
    def normalize_water_availability(raw_value: str) -> Optional[Tuple[str, str]]:
        """
        Normalize water availability statements
        
        Args:
            raw_value: Like "पाणी कमी आहे" or "water limited"
            
        Returns:
            Tuple of (level, format_type) or None
        """
        if not raw_value:
            return None
        
        raw_lower = raw_value.lower()
        
        # High patterns
        high_patterns = ['भरपूर', 'abundant', 'high', 'well', 'borewell', 'कुआँ', 'बोरवेल', 'लिमिटलेस']
        for pattern in high_patterns:
            if pattern.lower() in raw_lower:
                return ('high', 'high_pattern')
        
        # Low patterns
        low_patterns = ['कम', 'insufficient', 'low', 'limited', 'dry', 'drought', 'वर्षा', 'rainfall']
        for pattern in low_patterns:
            if pattern.lower() in raw_lower:
                return ('low', 'low_pattern')
        
        # Medium patterns
        medium_patterns = ['मध्यम', 'moderate', 'medium', 'seasonal', 'मौसमी', 'ऋतु']
        for pattern in medium_patterns:
            if pattern.lower() in raw_lower:
                return ('medium', 'medium_pattern')
        
        return None
    
    @staticmethod
    def normalize_experience_level(raw_value: str) -> Optional[Tuple[str, str]]:
        """
        Normalize experience level to standard values
        
        Args:
            raw_value: Like "नया" or "beginner" or "5 years" or "नया किसान"
            
        Returns:
            Tuple of (level, format_type) or None
        """
        if not raw_value:
            return None
        
        raw_lower = raw_value.lower()
        
        # Check for year/experience indicators FIRST (more specific than keywords)
        # Pattern: "N years", "N साल", "N वर्ष", "N अनुभव"
        years_patterns = [
            r'(\d+)\s*(?:year|साल|वर्ष|वर्षों|वर्षांचा|वर्षाचा)',
            r'(\d+)\s*(?:year|साल|वर्ष)',
            r'(\d+)\s*अनुभव'
        ]
        
        for pattern in years_patterns:
            years_match = re.search(pattern, raw_lower)
            if years_match:
                try:
                    years = int(years_match.group(1))
                    # Clarified thresholds:
                    # < 2 years = Beginner
                    # 2-10 years = Intermediate
                    # > 10 years = Expert
                    if years < 2:
                        return ('beginner', 'years_based')
                    elif years <= 10:
                        return ('intermediate', 'years_based')
                    else:
                        return ('expert', 'years_based')
                except (ValueError, IndexError):
                    continue
        
        # Check keyword mappings (fallback if no years mentioned)
        for level, keywords in EntityNormalizer.EXPERIENCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in raw_lower:
                    return (level, 'keyword_match')
        
        # Additional keyword matching for edge cases
        if any(word in raw_lower for word in ['नयचा', 'नया किसान', 'शुरुवातीचा', 'नई', 'नई किसान']):
            return ('beginner', 'keyword_match')
        elif any(word in raw_lower for word in ['अनुभवी', 'अनुभवी किसान', 'अनुभव']):
            return ('intermediate', 'keyword_match')
        elif any(word in raw_lower for word in ['विशेषज्ञ', 'expert', 'veteran']):
            return ('expert', 'keyword_match')
        
        return None
    
    @staticmethod
    def normalize_risk_tolerance(raw_value: str) -> Optional[Tuple[str, str]]:
        """
        Normalize risk tolerance to standard values
        
        Args:
            raw_value: Like "कम जोखीम" or "high risk"
            
        Returns:
            Tuple of (level, format_type) or None
        """
        if not raw_value:
            return None
        
        raw_lower = raw_value.lower()
        
        # Check keyword mappings
        for level, keywords in EntityNormalizer.RISK_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in raw_lower:
                    return (level, 'keyword_match')
        
        return None
    
    @staticmethod
    def normalize_time_availability(raw_value: str) -> Optional[Tuple[str, str]]:
        """
        Normalize time availability to standard values
        
        Args:
            raw_value: Like "पूरे दिन" or "part time"
            
        Returns:
            Tuple of (level, format_type) or None
        """
        if not raw_value:
            return None
        
        raw_lower = raw_value.lower()
        
        # Check keyword mappings
        for level, keywords in EntityNormalizer.TIME_AVAILABILITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in raw_lower:
                    return (level, 'keyword_match')
        
        return None
    
    @staticmethod
    def normalize_entity(entity_type: str, raw_value: Any) -> Dict[str, Any]:
        """
        Main normalization function - returns dict with raw and normalized values
        
        Args:
            entity_type: Type of entity (budget_rupees, land_size_hectares, etc)
            raw_value: Raw extracted value
            
        Returns:
            Dict with raw_value, normalized_value, normalization_confidence, notes
        """
        result = {
            'raw_value': raw_value,
            'normalized_value': None,
            'normalization_confidence': 0.0,
            'format_detected': None,
            'needs_clarification': False,
            'notes': ''
        }
        
        if raw_value is None:
            result['notes'] = 'Value was None'
            return result
        
        if entity_type == 'budget_rupees':
            normalized = EntityNormalizer.normalize_number(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = int(value)
                result['normalization_confidence'] = 0.95 if format_type == 'arabic_numeral' else 0.85
                result['format_detected'] = format_type
            else:
                result['needs_clarification'] = True
                result['notes'] = 'Could not parse number'
        
        elif entity_type == 'land_size_hectares':
            normalized = EntityNormalizer.normalize_land_size(str(raw_value))
            if normalized:
                value, unit_type = normalized
                result['normalized_value'] = round(value, 4)
                result['normalization_confidence'] = 0.95 if unit_type == 'hectare' else 0.90
                result['format_detected'] = unit_type
            else:
                result['needs_clarification'] = True
                result['notes'] = 'Could not parse land size'
        
        elif entity_type == 'location':
            normalized = EntityNormalizer.normalize_location(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = value
                result['normalization_confidence'] = 0.95 if format_type == 'exact_match' else 0.80
                result['format_detected'] = format_type
            else:
                result['needs_clarification'] = True
                result['notes'] = 'Could not normalize location'
        
        elif entity_type == 'time_numeric':
            normalized = EntityNormalizer.normalize_time_numeric(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = value
                result['normalization_confidence'] = 0.90
                result['format_detected'] = format_type
            else:
                result['needs_clarification'] = True
                result['notes'] = 'Could not parse time'
        
        elif entity_type == 'water_availability':
            normalized = EntityNormalizer.normalize_water_availability(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = value
                result['normalization_confidence'] = 0.85
                result['format_detected'] = format_type
            else:
                # If already a standard value, pass through
                if raw_value in ['high', 'medium', 'low']:
                    result['normalized_value'] = raw_value
                    result['normalization_confidence'] = 1.0
                    result['format_detected'] = 'standard_value'
                else:
                    result['needs_clarification'] = True
                    result['notes'] = 'Could not determine water level'
        
        elif entity_type == 'experience_level':
            normalized = EntityNormalizer.normalize_experience_level(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = value
                result['normalization_confidence'] = 0.85
                result['format_detected'] = format_type
            else:
                # If already a standard value, pass through
                if raw_value in ['beginner', 'intermediate', 'expert']:
                    result['normalized_value'] = raw_value
                    result['normalization_confidence'] = 1.0
                    result['format_detected'] = 'standard_value'
                else:
                    result['needs_clarification'] = True
                    result['notes'] = 'Could not determine experience level'
        
        elif entity_type == 'risk_tolerance':
            normalized = EntityNormalizer.normalize_risk_tolerance(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = value
                result['normalization_confidence'] = 0.85
                result['format_detected'] = format_type
            else:
                # If already a standard value, pass through
                if raw_value in ['low', 'medium', 'high']:
                    result['normalized_value'] = raw_value
                    result['normalization_confidence'] = 1.0
                    result['format_detected'] = 'standard_value'
                else:
                    result['needs_clarification'] = True
                    result['notes'] = 'Could not determine risk tolerance'
        
        elif entity_type == 'time_availability':
            normalized = EntityNormalizer.normalize_time_availability(str(raw_value))
            if normalized:
                value, format_type = normalized
                result['normalized_value'] = value
                result['normalization_confidence'] = 0.85
                result['format_detected'] = format_type
            else:
                # If already a standard value, pass through
                if raw_value in ['full_time', 'part_time', 'limited']:
                    result['normalized_value'] = raw_value
                    result['normalization_confidence'] = 1.0
                    result['format_detected'] = 'standard_value'
                else:
                    result['needs_clarification'] = True
                    result['notes'] = 'Could not determine time availability'
        
        else:
            # For other entity types, pass through as-is if already normalized
            if isinstance(raw_value, str):
                result['normalized_value'] = raw_value.lower()
                result['normalization_confidence'] = 0.8
            else:
                result['normalized_value'] = raw_value
                result['normalization_confidence'] = 0.9
        
        return result
