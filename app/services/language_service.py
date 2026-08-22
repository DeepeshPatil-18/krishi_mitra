"""Language Service - handles multilingual support"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LanguageService:
    """
    Handles language detection and translation.
    Preserves farmer language context.
    """

    SUPPORTED_LANGUAGES = ["marathi", "hindi", "english"]
    
    # Language code mappings for APIs
    LANGUAGE_CODES = {
        "marathi": "mr",
        "hindi": "hi",
        "english": "en",
    }

    def __init__(self):
        pass

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect language from text
        
        Args:
            text: Input text
            
        Returns:
            Language code (marathi, hindi, english)
        """
        # Simple heuristic-based detection
        # In production, use a proper language detection library like textblob or langdetect
        
        # Marathi script detection (Devanagari with specific patterns)
        marathi_indicators = ["ी", "ु", "े", "ो", "ा", "ृ"]
        marathi_count = sum(1 for char in text if char in marathi_indicators)
        
        # Hindi script detection (similar to Marathi but with different patterns)
        hindi_indicators = ["ु", "ी", "े", "ै", "ो", "ौ"]
        hindi_count = sum(1 for char in text if char in hindi_indicators)
        
        # If mostly English, return english
        if all(ord(char) < 128 for char in text if char.isalpha()):
            return "english"
        
        # Differentiate Marathi vs Hindi based on specific indicators
        if marathi_count > hindi_count:
            return "marathi"
        elif hindi_count > 0:
            return "hindi"
        else:
            return "english"

    @staticmethod
    def validate_language(language: str) -> bool:
        """Validate if language is supported"""
        return language.lower() in LanguageService.SUPPORTED_LANGUAGES

    @staticmethod
    def get_language_code(language: str) -> str:
        """Get standard language code for API calls"""
        lang_lower = language.lower()
        return LanguageService.LANGUAGE_CODES.get(lang_lower, "en")

    @staticmethod
    def translate(
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate text between languages
        
        Args:
            text: Text to translate
            source_language: Source language
            target_language: Target language
            
        Returns:
            Translated text
        """
        if source_language == target_language:
            return text
        
        # Placeholder for translation service (e.g., Google Translate)
        logger.warning(f"Translation from {source_language} to {target_language} not yet implemented")
        return text
