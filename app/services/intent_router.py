"""Intent Router - routes messages to appropriate services"""

import logging
from typing import Optional, Dict, Any
from app.schemas.intent import Intent

logger = logging.getLogger(__name__)


class IntentRouter:
    """
    Routes farmer messages to appropriate services based on intent.
    Uses deterministic rules first, falls back to AI only when necessary.
    """

    def __init__(self):
        pass

    @staticmethod
    def detect_intent(
        message: str,
        language: str = "marathi",
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[Intent, float, Dict[str, Any]]:
        """
        Detect intent from farmer message
        
        Args:
            message: Farmer's message
            language: Message language
            context: Additional context
            
        Returns:
            Tuple of (intent, confidence, extracted_parameters)
        """
        # Rule-based intent detection (deterministic, no AI required)
        # Order matters: check more specific intents first
        
        message_lower = message.lower()
        
        # SCHEME SEARCH - explicit government schemes/subsidy/help patterns
        scheme_patterns = [
            "सरकारी मदत", "सब्सिडी", "scheme", "subsidy", "योजना", "सहायता",
            "सरकार", "लाभ", "मदद", "subsidy", "आर्थिक मदद",
            "सरकारी योजना", "मुआवजा", "सहायक",
            "सरकार की योजना", "सरकारी सहायता"
        ]
        if any(pattern in message_lower for pattern in scheme_patterns):
            return Intent.SCHEME_SEARCH, 0.9, {}
        
        # MARKET SEARCH - where/how to sell, buyers, pricing, market info
        market_patterns = [
            "कुठे विकू", "बाजार", "buyer", "market", "sell", "विक्रय", "खरीदार",
            "विकून घेते", "विक्रेता", "कीमत", "भाव", "price",
            "मूल्य", "फायदेमंद", "profitable", "मुनाफा",
            "बिक्री", "कहाँ बिक", "कहां बेचूं", "खरीदार कहां",
            "कहाँ विकूँ", "बेचने के लिए", "विक्रय बाजार"
        ]
        if any(pattern in message_lower for pattern in market_patterns):
            return Intent.MARKET_SEARCH, 0.9, {}
        
        # EXPERT REQUEST - talk to expert, consultation
        expert_patterns = [
            "तज्ञ", "expert", "विशेषज्ञ", "पूछायचे", "ask",
            "सलाह", "advice", "मदद करून द्या", "मदद",
            "विशेषज्ञ सलाह", "सलाहकार", "परामर्श",
            "मुझे विशेषज्ञ", "किसी से सलाह"
        ]
        if any(pattern in message_lower for pattern in expert_patterns):
            return Intent.EXPERT_REQUEST, 0.85, {}
        
        # COMMUNITY - group, discussion, post, community
        community_patterns = [
            "समुदाय", "community", "पोस्ट", "post", "चर्चा", "discussion",
            "समूह", "ग्रुप", "group", "मिलकर", "सामूहिक",
            "चर्चाओं", "साथ", "अन्य किसान"
        ]
        if any(pattern in message_lower for pattern in community_patterns):
            return Intent.COMMUNITY, 0.85, {}
        
        # TRAINING REQUEST - learn, training, how to, guide, steps
        # Must be AFTER market/expert/scheme to avoid false positives
        training_patterns = [
            "कशी", "शेती", "खेती", "कसे करू", "कैसे करूं", "how to",
            "training", "guide", "सिकू", "सिखायचे", "सीखना",
            "सिख", "प्रशिक्षण", "सीखें", "सीख", "शिक्षा",
            "steps", "प्रक्रिया", "विधि", "तरीका",
            "कैसे शुरू", "कसे शुरू", "तरीके", "पद्धति",
            "learn", "training", "how", "steps", "process",
            "कितना", "खर्च", "cost", "investment", "निवेश", "लागत",
            "जोखिम क्या", "काय आहे जोखिम", "risk"
        ]
        # Don't match if it's asking "what business for my situation"
        livelihood_indicators = ["सुरू", "व्यवसाय", "काय", "कोण सा", "कौन सा", "कौन", "कोण", "कोणता", "कौनसा", "कोणते", "कौनसे"]
        has_livelihood_indicator = any(word in message_lower for word in livelihood_indicators)
        
        if any(pattern in message_lower for pattern in training_patterns) and not has_livelihood_indicator:
            return Intent.TRAINING_REQUEST, 0.85, {}
        
        # LIVELIHOOD RECOMMENDATION - asking what business/farming for their situation
        # This is the PRIMARY use case for farmers
        livelihood_patterns = [
            # Direct questions: what should I do/start
            "काय सुरू करू", "काय करू", "कोण सा व्यवसाय", "कौन सा व्यवसाय",
            "कौन सा काम", "कोणते करावे", "कौनसे करूं", "कोणता चांगला",
            "कौन सा अच्छा", "कौन सा सही", "कोणता योग्य",
            "कैसे शुरू करूं", "कसे सुरू करू", "क्या करूं", "का करु",
            "कैसे काम करूं", "क्या व्यवसाय", "कोण सा शेती",
            "व्यवसाय सुरू करायचे", "व्यवसाय शुरू करना", "काम शुरू करना",
            "which business", "what business", "what farming", "what crop",
            "should i start", "can i start", "should i do", "should i grow",
            
            # Implied recommendations through constraints
            "बजेट आहे", "बजेट हैं", "budget है", "budget have",
            "जमीन आहे", "जमीन है", "land है", "एकर आहे", "एकड़ है",
            "पाणी", "पानी", "water",
            "अनुभव", "experience",
            "समय आहे", "समय है", "time है", "i have",
            
            # Asking if something is good/possible/feasible
            "चांगली आहे", "अच्छा है", "ठीक है", "ठीक हैं",
            "शक्य आहे", "संभव है", "possible है",
            "होईल", "होगा", "will", "काम करेल",
            "मुनाफा", "फायदा", "लाभ", "फायदेमंद",
            "is it good", "is it profitable", "is it possible",
            
            # Statement + question about specific enterprise
            "करायचे आहे", "करना है", "करना चाहता", "करू इच्छितो",
            "करायचे", "करू चाहता", "चाहता हूँ", "इच्छा आहे",
            "तयार आहे", "तैयार हूँ", "willing",
            "want to", "like to", "interested in",
            
            # Just giving constraints (budget, land, experience) + asking what
            "आहेत.*काय", "है.*क्या", "have.*what"
        ]
        if any(pattern in message_lower for pattern in livelihood_patterns):
            return Intent.LIVELIHOOD_RECOMMENDATION, 0.8, {}
        
        # If multiple constraints mentioned without explicit question word, likely livelihood
        constraint_keywords = ["हजार", "लाख", "rupees", "रुपये", "एकर", "एकड़", "hectare", "हेक्टर",
                               "पाणी", "पानी", "water", "अनुभव", "experience", "बजेट", "budget",
                               "समय", "time", "जमीन", "land", "enterprise", "have"]
        constraint_count = sum(1 for kw in constraint_keywords if kw.lower() in message_lower)
        if constraint_count >= 2 and "?" in message:
            # Multiple constraints + question mark = likely livelihood
            return Intent.LIVELIHOOD_RECOMMENDATION, 0.75, {}
        
        # Default to general question
        return Intent.GENERAL_QUESTION, 0.5, {}

    @staticmethod
    def extract_parameters(
        message: str,
        intent: Intent,
        language: str = "marathi",
    ) -> Dict[str, Any]:
        """
        Extract parameters from message based on intent
        
        Args:
            message: Farmer's message
            intent: Detected intent
            language: Message language
            
        Returns:
            Dictionary of extracted parameters
        """
        params = {}
        
        if intent == Intent.LIVELIHOOD_RECOMMENDATION:
            # Try to extract budget, land size, etc.
            # Simple regex-based extraction
            import re
            budget_match = re.search(r"(\d+)\s*(हजार|thousand|rupees|रुपये)", message, re.IGNORECASE)
            if budget_match:
                params["budget"] = int(budget_match.group(1)) * 1000  # Convert to full amount
        
        elif intent == Intent.MARKET_SEARCH:
            # Extract product name
            if any(word in message.lower() for word in ["मध", "शहद", "honey"]):
                params["product"] = "honey"
            elif any(word in message.lower() for word in ["अंडे", "egg"]):
                params["product"] = "eggs"
        
        return params
