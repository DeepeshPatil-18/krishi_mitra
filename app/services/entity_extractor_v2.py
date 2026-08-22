"""
Entity Extractor V2 - Enhanced extraction with normalization and preservation of raw values

This is a BRIDGE layer that:
1. Uses existing entity_extractor.py for extraction
2. Applies entity_normalizer.py for normalization
3. Preserves raw values alongside normalized values
4. Returns rich metadata (confidence, format detected, needs_clarification)
5. Maintains backward compatibility with existing code
"""

import logging
from typing import Dict, Any, Optional
from app.services.entity_extractor import EntityExtractor
from app.services.entity_normalizer import EntityNormalizer

logger = logging.getLogger(__name__)


class EntityExtractorV2:
    """Enhanced entity extraction with normalization and metadata"""
    
    # Entity types that have normalization defined
    NORMALIZABLE_ENTITIES = {
        'budget_rupees',
        'land_size_hectares',
        'location',
        'time_numeric',
        'water_availability',
        'experience_level',
        'risk_tolerance',
        'time_availability'
    }
    
    # Entities that need special handling for raw value preservation
    CATEGORICAL_ENTITIES = {
        'water_availability',
        'experience_level',
        'risk_tolerance',
        'time_availability',
        'enterprise'
    }
    
    @staticmethod
    def extract_all(message: str, language: str = 'auto') -> Dict[str, Any]:
        """
        Extract all entities with normalization and preservation of raw values.
        
        Returns dict with structure:
        {
            'budget_rupees': {
                'extracted': 50000,  # Raw value from extractor
                'normalized': 50000,  # Normalized value
                'raw_text': '50 हजार',  # Original text if available
                'confidence': 0.95,
                'format': 'arabic_numeral' or 'marathi_words', etc
                'needs_clarification': False
            },
            'location': {
                'extracted': 'maharashtra',
                'normalized': 'nashik',  # IMPROVED: returns district not state
                'raw_text': 'नाशिकमध्ये',
                'confidence': 0.85,
                'format': 'district_name',
                'needs_clarification': False
            },
            ...
            '_metadata': {
                'extraction_timestamp': '...',
                'language_detected': 'marathi',
                'total_entities': 3,
                'high_confidence_count': 2,
                'needs_clarification_count': 0
            }
        }
        """
        
        # Step 1: Extract using existing EntityExtractor
        extracted_raw = EntityExtractor.extract_all(message, language=language)
        
        # Step 2: Normalize and preserve raw values
        result = {}
        high_confidence_count = 0
        needs_clarification_count = 0
        
        for entity_type, raw_value in extracted_raw.items():
            # Normalize the value
            normalization_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
            
            # Build enriched entity record
            entity_record = {
                'extracted': raw_value,  # Original extracted value
                'normalized': normalization_result.get('normalized_value'),
                'raw_text': None,  # Would come from extractor if available
                'confidence': normalization_result.get('normalization_confidence', 0.0),
                'format': normalization_result.get('format_detected'),
                'needs_clarification': normalization_result.get('needs_clarification', False),
                'notes': normalization_result.get('notes', '')
            }
            
            result[entity_type] = entity_record
            
            # Track confidence
            if entity_record['confidence'] >= 0.8:
                high_confidence_count += 1
            if entity_record['needs_clarification']:
                needs_clarification_count += 1
        
        # Add metadata
        result['_metadata'] = {
            'extraction_timestamp': None,  # Could add timestamp
            'language_detected': language,
            'total_entities': len(extracted_raw),
            'high_confidence_count': high_confidence_count,
            'needs_clarification_count': needs_clarification_count
        }
        
        return result
    
    @staticmethod
    def get_normalized_value(entity_type: str, raw_value: Any) -> Optional[Any]:
        """
        Quick access to just the normalized value (for backward compatibility).
        
        Returns None if cannot normalize or if value is ambiguous.
        """
        normalization_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
        
        if normalization_result.get('needs_clarification'):
            # Return None rather than guessing
            return None
        
        return normalization_result.get('normalized_value')
    
    @staticmethod
    def extract_with_confidence_threshold(message: str, language: str = 'auto', min_confidence: float = 0.8) -> Dict[str, Any]:
        """
        Extract entities only above a confidence threshold.
        
        Returns only entities with confidence >= min_confidence.
        Useful for being conservative with recommendations.
        """
        full_results = EntityExtractorV2.extract_all(message, language=language)
        
        # Remove metadata first
        metadata = full_results.pop('_metadata', {})
        
        # Filter by confidence
        filtered_results = {
            k: v for k, v in full_results.items()
            if v.get('confidence', 0) >= min_confidence and not v.get('needs_clarification', False)
        }
        
        # Add back metadata
        filtered_results['_metadata'] = {
            **metadata,
            'confidence_threshold': min_confidence,
            'entities_filtered_out': len(full_results) - len(filtered_results)
        }
        
        return filtered_results


# Backward compatibility wrapper
def extract_all_entities(message: str, language: str = 'auto') -> Dict[str, Any]:
    """
    Backward compatible wrapper that returns normalized values only.
    
    For code that expects the old format, this returns:
    {
        'budget_rupees': 50000,
        'land_size_hectares': 0.8094,
        'location': 'nashik',
        ...
    }
    """
    results = EntityExtractorV2.extract_all(message, language=language)
    
    # Extract just normalized values
    simplified = {}
    for key, value in results.items():
        if key != '_metadata' and isinstance(value, dict):
            normalized = value.get('normalized')
            if normalized is not None:
                simplified[key] = normalized
    
    return simplified
