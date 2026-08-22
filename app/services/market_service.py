"""
Market Price Search Service — Real-time agricultural commodity market prices.

Uses official Government of India data.gov.in AGMARKNET API as primary source.
Falls back to cached official market data if API unavailable.

Features:
- Live price queries from AGMARKNET portal
- Multilingual commodity/location matching
- Graceful fallback to cached data
- Clear labelling of data source (LIVE vs CACHED)
"""

import json
import logging
import os
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MarketPrice:
    """Commodity market price result"""
    commodity: str
    market: str
    location: str  # State/district
    date: str  # Date of price
    min_price: float
    max_price: float
    modal_price: float
    unit: str  # Usually quintal (qtl)
    source: str  # "LIVE" or "CACHED"
    source_name: str  # "data.gov.in/AGMARKNET" or similar
    source_url: Optional[str] = None


class MarketService:
    """Service for fetching and searching commodity market prices"""

    # Cached fallback data loaded on init
    _CACHED_DATA = None

    # Commodity name mappings (English ↔ Hindi ↔ Marathi)
    COMMODITY_ALIASES = {
        # Vegetables
        "onion": ["प्याज", "कांदा", "pyaaz", "kanda"],
        "tomato": ["टमाटर", "टोमॅटो", "virangai"],
        "potato": ["आलू", "बटाटा", "aloo", "batata"],
        "cabbage": ["पत्तागोभी", "कोबी", "patta_gobhi"],
        "carrot": ["गाजर", "गाजर", "gajar"],
        "cauliflower": ["फूलगोभी", "फूलकोबी", "phool_gobhi"],
        
        # Grains
        "wheat": ["गेहूँ", "गोधूम", "gehun"],
        "rice": ["चावल", "तांदुळ", "chawal"],
        "maize": ["मक्का", "मक्का", "makka"],
        "jowar": ["ज्वार", "ज्वार", "jowar"],
        "bajra": ["बाजरा", "बाजरा", "bajra"],
        
        # Pulses
        "chickpea": ["चना", "हरभरा", "chana"],
        "dal": ["दाल", "दाळ", "dal"],
        "lentil": ["मसूर", "मसूर", "masur"],
        "tur": ["तूर", "तुरई", "tur"],
        
        # Others
        "soybean": ["सोयाबीन", "सोयाबीन", "soybean"],
        "cotton": ["कपास", "कपास", "kapas"],
        "sugarcane": ["गन्ना", "ऊस", "ganna"],
    }

    # Location aliases (to standardize state/market names)
    LOCATION_ALIASES = {
        "nashik": "nashik",
        "नाशिक": "nashik",
        "नासिक": "nashik",
        "maharashtra": "maharashtra",
        "महाराष्ट्र": "maharashtra",
        "pune": "pune",
        "पुणे": "pune",
        "mumbai": "mumbai",
        "मुंबई": "mumbai",
        "aurangabad": "aurangabad",
        "औरंगाबाद": "aurangabad",
    }

    @classmethod
    def _load_cached_data(cls) -> List[Dict[str, Any]]:
        """Load cached fallback market data from JSON file"""
        if cls._CACHED_DATA is not None:
            return cls._CACHED_DATA

        file_path = Path(__file__).parent.parent / "data" / "market_prices_cache.json"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls._CACHED_DATA = data.get("prices", [])
                logger.info(f"Loaded {len(cls._CACHED_DATA)} cached market prices")
                return cls._CACHED_DATA
        except FileNotFoundError:
            logger.warning(f"Cached market data not found at {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in cached market data: {e}")
            return []

    @classmethod
    def _fetch_from_live_api(
        cls,
        commodity: str,
        location: str = "maharashtra"
    ) -> List[MarketPrice]:
        """
        Fetch live prices from official data.gov.in AGMARKNET API.
        
        Returns list of MarketPrice or empty list if API unavailable.
        """
        api_key = os.getenv("AGMARKNET_API_KEY")
        if not api_key:
            logger.debug("No AGMARKNET_API_KEY in environment; will use cached data")
            return []

        try:
            # Official endpoint: api.data.gov.in
            url = "https://api.data.gov.in/resources/current-daily-price-various-commodities-various-markets-mandis/api"
            
            params = {
                "api-key": api_key,
                "format": "json",
                "filters[commodity]": commodity,
                "filters[state]": location,
                "limit": 100,
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            records = data.get("records", [])

            results = []
            for record in records:
                try:
                    price = MarketPrice(
                        commodity=record.get("commodity", ""),
                        market=record.get("market", ""),
                        location=record.get("state", location),
                        date=record.get("arrival_date", datetime.now().strftime("%Y-%m-%d")),
                        min_price=float(record.get("min_price", 0)),
                        max_price=float(record.get("max_price", 0)),
                        modal_price=float(record.get("modal_price", 0)),
                        unit=record.get("unit", "qtl"),
                        source="LIVE",
                        source_name="data.gov.in/AGMARKNET",
                        source_url="https://agmarknet.gov.in/",
                    )
                    results.append(price)
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping malformed API record: {e}")
                    continue

            logger.info(f"Fetched {len(results)} live prices for {commodity} in {location}")
            return results

        except requests.exceptions.Timeout:
            logger.warning("API request timed out; will use cached data")
            return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed ({e}); will use cached data")
            return []
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse API response: {e}")
            return []

    @classmethod
    def _search_cached_data(
        cls,
        commodity: str,
        location: str = "maharashtra"
    ) -> List[MarketPrice]:
        """
        Search cached fallback market data.
        
        Returns list of MarketPrice from cached dataset.
        """
        cached = cls._load_cached_data()
        if not cached:
            return []

        commodity_lower = commodity.lower()
        location_lower = location.lower()

        results = []
        for record in cached:
            rec_commodity = record.get("commodity", "").lower()
            rec_location = record.get("location", "").lower()

            # Match commodity (exact or alias)
            commodity_match = (
                commodity_lower in rec_commodity or
                rec_commodity in commodity_lower or
                any(alias in commodity_lower for alias in cls.COMMODITY_ALIASES.get(commodity_lower, []))
            )

            # Match location
            location_match = (
                location_lower in rec_location or
                rec_location in location_lower
            )

            if commodity_match and location_match:
                try:
                    price = MarketPrice(
                        commodity=record.get("commodity", ""),
                        market=record.get("market", ""),
                        location=record.get("location", location),
                        date=record.get("date", "unknown"),
                        min_price=float(record.get("min_price", 0)),
                        max_price=float(record.get("max_price", 0)),
                        modal_price=float(record.get("modal_price", 0)),
                        unit=record.get("unit", "qtl"),
                        source="CACHED",
                        source_name="Historical AGMARKNET Data",
                        source_url="https://agmarknet.gov.in/",
                    )
                    results.append(price)
                except (ValueError, KeyError):
                    continue

        return results

    @classmethod
    def search_prices(
        cls,
        commodity: str,
        location: str = "maharashtra",
        limit: int = 5
    ) -> List[MarketPrice]:
        """
        Search for commodity prices in a location.
        
        Args:
            commodity: Commodity name (English/Hindi/Marathi)
            location: Location/market (default: Maharashtra)
            limit: Max results to return
        
        Returns:
            List of MarketPrice objects (live, then cached)
        """
        if not commodity or not commodity.strip():
            logger.warning("Empty commodity query")
            return []

        # Normalize inputs
        commodity_normalized = commodity.strip().lower()
        location_normalized = cls.LOCATION_ALIASES.get(location.lower(), location.lower())

        # Try live API first
        live_results = cls._fetch_from_live_api(commodity_normalized, location_normalized)
        if live_results:
            return live_results[:limit]

        # Fall back to cached data
        logger.info("Live API unavailable; using cached data")
        cached_results = cls._search_cached_data(commodity_normalized, location_normalized)
        return cached_results[:limit]

    @classmethod
    def format_results(
        cls,
        results: List[MarketPrice],
        language: str = "english"
    ) -> str:
        """
        Format market prices for farmer-friendly display.
        
        Args:
            results: List of MarketPrice
            language: "english", "hindi", or "marathi"
        
        Returns:
            Formatted response string
        """
        if not results:
            if language == "marathi":
                return "या कमोडिटीचे बाजार भाव उपलब्ध नाहीत. कृपया AGMARKNET किंवा अधिकृत बाजार पोर्टल तपासा."
            elif language == "hindi":
                return "इस कमोडिटी के बाजार भाव उपलब्ध नहीं हैं। कृपया AGMARKNET या आधिकारिक बाजार पोर्टल देखें।"
            else:
                return "Market prices not available for this commodity. Please check AGMARKNET or official market portal."

        # Format header with source info
        if results and results[0].source == "LIVE":
            if language == "marathi":
                header = f"🔴 लाइव बाजार भाव (आज):\n\n"
            elif language == "hindi":
                header = f"🔴 लाइव बाजार भाव (आज):\n\n"
            else:
                header = f"🔴 Live Market Prices (Today):\n\n"
        else:
            if language == "marathi":
                header = f"⚪ कॅश बाजार भाव (संदर्भ):\n\n"
            elif language == "hindi":
                header = f"⚪ कैश बाजार भाव (संदर्भ):\n\n"
            else:
                header = f"⚪ Reference Market Prices:\n\n"

        formatted = [header]

        for idx, result in enumerate(results, 1):
            if language == "marathi":
                entry = (
                    f"{idx}. {result.commodity.title()}\n"
                    f"   बाजार: {result.market}\n"
                    f"   तारीख: {result.date}\n"
                    f"   किमान: ₹{result.min_price}/qtl\n"
                    f"   कमाल: ₹{result.max_price}/qtl\n"
                    f"   मोडल: ₹{result.modal_price}/qtl\n"
                )
            elif language == "hindi":
                entry = (
                    f"{idx}. {result.commodity.title()}\n"
                    f"   मंडी: {result.market}\n"
                    f"   तारीख: {result.date}\n"
                    f"   न्यूनतम: ₹{result.min_price}/qtl\n"
                    f"   अधिकतम: ₹{result.max_price}/qtl\n"
                    f"   मॉडल: ₹{result.modal_price}/qtl\n"
                )
            else:
                entry = (
                    f"{idx}. {result.commodity.title()}\n"
                    f"   Market: {result.market}\n"
                    f"   Date: {result.date}\n"
                    f"   Min: ₹{result.min_price}/qtl\n"
                    f"   Max: ₹{result.max_price}/qtl\n"
                    f"   Modal: ₹{result.modal_price}/qtl\n"
                )

            formatted.append(entry)

        # Add source disclaimer
        if results and results[0].source == "CACHED":
            if language == "marathi":
                disclaimer = (
                    f"\n⚠️ ही भाव संदर्भ डेटा आहे (लाइव नाही). "
                    f"वर्तमान भाव AGMARKNET किंवा {results[0].source_name} येथे तपासा."
                )
            elif language == "hindi":
                disclaimer = (
                    f"\n⚠️ ये भाव संदर्भ डेटा हैं (लाइव नहीं)। "
                    f"वर्तमान भाव AGMARKNET या {results[0].source_name} पर देखें।"
                )
            else:
                disclaimer = (
                    f"\n⚠️ These are reference prices (not live). "
                    f"Check AGMARKNET or {results[0].source_name} for current prices."
                )
            formatted.append(disclaimer)

        return "\n".join(formatted)

    @classmethod
    def normalize_commodity(cls, text: str) -> Optional[str]:
        """
        Normalize user input to known commodity name.
        
        Returns commodity name or None if not recognized.
        """
        text_lower = text.lower()

        # Direct match
        if text_lower in cls.COMMODITY_ALIASES:
            return text_lower

        # Alias match
        for commodity, aliases in cls.COMMODITY_ALIASES.items():
            if text_lower in aliases or any(alias in text_lower for alias in aliases):
                return commodity

        return None

    @classmethod
    def normalize_location(cls, text: str) -> str:
        """Normalize location name to standard form."""
        text_lower = text.lower()
        return cls.LOCATION_ALIASES.get(text_lower, text_lower)
