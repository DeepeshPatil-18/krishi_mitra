"""Temporary data provider - loads fixture data from JSON files"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Data cache - loaded once on import
_DATA_CACHE = {}


def _load_json_file(filename: str) -> Dict[str, Any]:
    """Load JSON file from data directory"""
    if filename in _DATA_CACHE:
        return _DATA_CACHE[filename]
    
    file_path = Path(__file__).parent.parent / "data" / filename
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _DATA_CACHE[filename] = data
            return data
    except FileNotFoundError:
        logger.error(f"Data file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filename}: {e}")
        return {}


class EnterpriseProvider:
    """Provides enterprise data from temporary JSON storage"""
    
    @staticmethod
    def get_all_enterprises() -> List[Dict[str, Any]]:
        """Get all enterprises"""
        data = _load_json_file("enterprises.json")
        return data.get("enterprises", [])
    
    @staticmethod
    def get_enterprise_by_code(code: str) -> Optional[Dict[str, Any]]:
        """Get specific enterprise by code"""
        enterprises = EnterpriseProvider.get_all_enterprises()
        for ent in enterprises:
            if ent.get("code") == code:
                return ent
        return None
    
    @staticmethod
    def get_enterprises_by_codes(codes: List[str]) -> List[Dict[str, Any]]:
        """Get multiple enterprises by codes"""
        enterprises = EnterpriseProvider.get_all_enterprises()
        return [ent for ent in enterprises if ent.get("code") in codes]


class SchemeProvider:
    """Provides scheme data from temporary JSON storage"""
    
    @staticmethod
    def get_all_schemes() -> List[Dict[str, Any]]:
        """Get all schemes"""
        data = _load_json_file("schemes.json")
        return data.get("schemes", [])
    
    @staticmethod
    def get_schemes_by_enterprise(enterprise: str, state: str = "maharashtra") -> List[Dict[str, Any]]:
        """Get schemes relevant to an enterprise"""
        schemes = SchemeProvider.get_all_schemes()
        return [
            s for s in schemes
            if (s.get("enterprise") == enterprise or s.get("enterprise") == "general")
            and (s.get("state") == state or s.get("state") == "all_india")
            and s.get("is_active", True)
        ]


class TrainingProvider:
    """Provides training module data from temporary JSON storage"""
    
    @staticmethod
    def get_all_training_modules() -> List[Dict[str, Any]]:
        """Get all training modules"""
        data = _load_json_file("training_modules.json")
        return data.get("training_modules", [])
    
    @staticmethod
    def get_training_by_enterprise(enterprise: str, language: str = "marathi") -> List[Dict[str, Any]]:
        """Get training modules for an enterprise"""
        modules = TrainingProvider.get_all_training_modules()
        return [
            m for m in modules
            if m.get("enterprise") == enterprise
            and m.get("language") == language
        ]


class MarketProvider:
    """Provides market data from temporary JSON storage"""
    
    @staticmethod
    def get_all_markets() -> List[Dict[str, Any]]:
        """Get all market opportunities"""
        data = _load_json_file("markets.json")
        return data.get("markets", [])
    
    @staticmethod
    def get_markets_by_enterprise(enterprise: str) -> List[Dict[str, Any]]:
        """Get market opportunities for an enterprise"""
        markets = MarketProvider.get_all_markets()
        return [m for m in markets if m.get("enterprise") == enterprise]
    
    @staticmethod
    def get_markets_by_product(product: str) -> List[Dict[str, Any]]:
        """Get market opportunities for a product"""
        markets = MarketProvider.get_all_markets()
        return [m for m in markets if product.lower() in m.get("product", "").lower()]


class ExpertProvider:
    """Provides expert data from temporary JSON storage"""
    
    @staticmethod
    def get_all_experts() -> List[Dict[str, Any]]:
        """Get all experts"""
        data = _load_json_file("experts.json")
        return data.get("experts", [])
    
    @staticmethod
    def get_experts_by_expertise(expertise: str) -> List[Dict[str, Any]]:
        """Get experts with specific expertise"""
        experts = ExpertProvider.get_all_experts()
        return [
            e for e in experts
            if expertise in e.get("expertise", [])
            and e.get("is_active", False)
        ]
    
    @staticmethod
    def get_experts_by_language(language: str) -> List[Dict[str, Any]]:
        """Get experts who speak a specific language"""
        experts = ExpertProvider.get_all_experts()
        return [
            e for e in experts
            if language in e.get("languages", [])
            and e.get("is_active", False)
        ]
