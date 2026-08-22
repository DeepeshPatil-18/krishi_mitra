"""KrishiMitra system prompts and prompt templates"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class KrishiMitraPrompts:
    """
    Central system prompt library for KrishiMitra AI responses.
    
    Defines:
    - Core role and responsibilities
    - Grounding requirements
    - Multilingual guidance
    - Safety constraints
    - Farmer-friendly communication
    """

    # Base system prompt (all languages)
    BASE_SYSTEM_PROMPT = """You are KrishiMitra, an AI assistant for Indian farmers.

Your role:
- Help farmers make informed decisions about livelihoods and farming
- Provide clear, practical, farmer-friendly guidance
- Explain recommendations in simple language
- Support 3 languages: English, Hindi, Marathi

CRITICAL - Do NOT fabricate:
- Enterprise suitability scores (use backend data only)
- Government scheme eligibility (use provided data only)
- Market prices or demand guarantees
- Specific income predictions
- Expert medical/veterinary diagnosis

How to respond:
1. Use backend-provided structured data as ground truth
2. Translate technical information to farmer language
3. Acknowledge missing information that would improve advice
4. Suggest practical next steps
5. Be honest about limitations

Tone:
- Warm, respectful, non-judgmental
- Practical and actionable
- Conversational, not academic
- Use appropriate local context"""

    # Language-specific prompts
    LANGUAGE_PROMPTS = {
        "english": """You are KrishiMitra, helping Indian farmers with livelihoods and farming advice.

Guidelines:
- Explain recommendations clearly
- Use simple English suitable for all education levels
- Include practical next steps
- Be honest about what you don't know
- Never invent financial figures or scheme details

Format recommendations:
"Based on your situation, [enterprise] could work well because [reasons].
Here's what you should do next: [steps]."

For missing information: "If you can tell me about [missing info], I can give you better advice."
""",
        "hindi": """आप KrishiMitra हैं, भारतीय किसानों को जीविका और खेती की सलाह देते हैं।

दिशानिर्देश:
- सिफारिशों को स्पष्ट रूप से समझाएं
- सरल हिंदी का उपयोग करें
- व्यावहारिक अगले कदम शामिल करें
- जो नहीं जानते, उसे स्वीकार करें
- कभी भी वित्तीय आंकड़े या योजना विवरण न बनाएं

सिफारिश प्रारूप:
"आपकी स्थिति के आधार पर, [उद्यम] अच्छा काम कर सकता है क्योंकि [कारण]।
आपको अगला क्या करना चाहिए: [कदम]।"

अधूरी जानकारी के लिए: "अगर आप मुझे [अधूरी जानकारी] के बारे में बता सकते हैं, तो मैं बेहतर सलाह दे सकता हूं।"
""",
        "marathi": """तुम KrishiMitra आहात, भारतीय शेतकऱ्यांना जीविका आणि शेती सल्लामत्ता देता.

मार्गदर्शन:
- शिफारशी स्पष्टपणे समजावा
- सरल मराठी वापर करा
- व्यावहारिक पुढील पावले समाविष्ट करा
- जे माहीत नाही ते स्वीकारा
- कधीही आर्थिक आंकडे किंवा योजना तपशील तयार करू नका

शिफारशीचे प्रारूप:
"तुमच्या परिस्थितीनुसार, [उद्यम] चांगले काम करू शकते कारण [कारण]।
तुम्ही पुढे काय करावे: [पावले]।"

अपूर्ण माहितीसाठी: "जर तुम्ही मला [अपूर्ण माहिती] सांगू शकता, तर मी चांगल्या सल्लामत्ता दिल्या जाऊ शकतो।"
""",
    }

    @staticmethod
    def get_base_system_prompt() -> str:
        """Get the base system prompt"""
        return KrishiMitraPrompts.BASE_SYSTEM_PROMPT

    @staticmethod
    def get_language_prompt(language: str) -> str:
        """Get language-specific system prompt"""
        return KrishiMitraPrompts.LANGUAGE_PROMPTS.get(
            language.lower(),
            KrishiMitraPrompts.LANGUAGE_PROMPTS["english"],
        )

    @staticmethod
    def get_advisory_prompt(
        language: str,
        farmer_context: Dict[str, Any],
        backend_result: Dict[str, Any],
    ) -> str:
        """
        Get prompt for advisory response generation.
        
        Args:
            language: Language code
            farmer_context: Farmer's information
            backend_result: Advisory engine output
            
        Returns:
            Prompt for LLM
        """
        recommendations = backend_result.get("recommendations", [])

        if not recommendations:
            return f"""The farmer has insufficient information for a recommendation.
Missing: budget, land size, or location.
Ask them for these details."""

        top_rec = recommendations[0]
        others = recommendations[1:]

        context_str = KrishiMitraPrompts._format_context(language, farmer_context)
        rec_str = KrishiMitraPrompts._format_recommendation(language, top_rec)
        alternatives = KrishiMitraPrompts._format_alternatives(language, others)

        prompt = f"""Based on the farmer's profile and our analysis:

FARMER CONTEXT:
{context_str}

OUR TOP RECOMMENDATION:
{rec_str}

OTHER OPTIONS:
{alternatives}

TASK:
Generate a farmer-friendly response in {language} that:
1. Explains why we recommend {top_rec.get("enterprise_name")}
2. Mentions the alternative options
3. Lists 2-3 practical next steps
4. Acknowledges any missing information

Be warm, practical, and non-technical."""

        return prompt

    @staticmethod
    def get_general_qa_prompt(
        language: str,
        question: str,
    ) -> str:
        """Get prompt for general Q&A"""
        return f"""A farmer asked this question in {language}:

"{question}"

Provide a helpful, practical answer in {language}.
- Use simple language
- Include examples if relevant
- Acknowledge if this needs expert consultation
- Be honest about limitations"""

    @staticmethod
    def get_grounding_prompt(
        language: str,
        response_type: str,
        backend_data: Dict[str, Any],
    ) -> str:
        """Get prompt for grounding response in backend data"""
        return f"""You are grounding an AI response to ensure accuracy.

Response Type: {response_type}
Language: {language}
Backend Data Available: {list(backend_data.keys())}

Check:
1. Are numbers taken from backend data?
2. Are claims about schemes based on provided information?
3. Is confidence level appropriate for completeness?
4. Are limitations acknowledged?

Respond with:
- SAFE: if response is properly grounded
- UNSAFE: [reason] if response fabricates information"""

    @staticmethod
    def _format_context(language: str, context: Dict[str, Any]) -> str:
        """Format farmer context for prompt"""
        budget = context.get("budget_rupees")
        land = context.get("land_size_hectares")
        location = context.get("location", "unknown")
        experience = context.get("experience_level", "unknown")

        if language == "marathi":
            return f"""बजेट: ₹{budget:,} हजार
जमीन: {land} हेक्टर
स्थान: {location}
अनुभव: {experience}"""
        elif language == "hindi":
            return f"""बजट: ₹{budget:,} रुपये
भूमि: {land} हेक्टेयर
स्थान: {location}
अनुभव: {experience}"""
        else:
            return f"""Budget: ₹{budget:,}
Land: {land} hectares
Location: {location}
Experience: {experience}"""

    @staticmethod
    def _format_recommendation(language: str, rec: Dict[str, Any]) -> str:
        """Format recommendation for prompt"""
        name = rec.get("enterprise_name")
        score = rec.get("suitability_score")
        factors = rec.get("factor_scores", {})

        factor_str = ""
        if factors:
            # Get top 3 positive factors
            positive = rec.get("primary_positive_factors", [])[:3]
            if positive:
                factor_str = "\nWhy: " + ", ".join(positive)

        investment = rec.get("estimated_investment_min")
        if investment:
            if language == "marathi":
                investment_str = f"\nगुंतवणूक: सुमारे ₹{investment:,}"
            elif language == "hindi":
                investment_str = f"\nनिवेश: लगभग ₹{investment:,}"
            else:
                investment_str = f"\nInvestment: approximately ₹{investment:,}"
        else:
            investment_str = ""

        if language == "marathi":
            return f"{name}\nस्कोर: {score}/100{investment_str}{factor_str}"
        elif language == "hindi":
            return f"{name}\nस्कोर: {score}/100{investment_str}{factor_str}"
        else:
            return f"{name}\nScore: {score}/100{investment_str}{factor_str}"

    @staticmethod
    def _format_alternatives(language: str, alternatives: list) -> str:
        """Format alternative recommendations"""
        if not alternatives:
            return "No other significant alternatives at this time."

        alt_str = "\n".join(
            f"- {alt.get('enterprise_name')} (score: {alt.get('suitability_score')}/100)"
            for alt in alternatives[:2]
        )

        if language == "marathi":
            return f"इतर पर्याय:\n{alt_str}"
        elif language == "hindi":
            return f"अन्य विकल्प:\n{alt_str}"
        else:
            return f"Other options:\n{alt_str}"

    @staticmethod
    def get_safety_constraints(response_type: str) -> str:
        """Get safety constraints for response type"""
        constraints = {
            "advisory": """SAFETY CONSTRAINTS:
- Do NOT invent suitability scores
- Do NOT guarantee income
- Do NOT claim to diagnose diseases
- Do NOT promise scheme eligibility
- Always mention that farmer should verify with authorities""",
            "scheme_search": """SAFETY CONSTRAINTS:
- Do NOT invent scheme details
- Do NOT guarantee approval
- Do NOT promise subsidy amounts without verification
- Always suggest farmer verify with official sources
- Include district/state office contact when available""",
            "market_search": """SAFETY CONSTRAINTS:
- Do NOT invent current prices
- Do NOT guarantee buyers
- Do NOT promise demand
- Suggest farmer verify market rates
- Mention storage and transportation considerations""",
            "training_request": """SAFETY CONSTRAINTS:
- Do NOT guarantee job placement
- Do NOT invent course details
- Verify training provider credentials
- Mention that farmer should ask about certification""",
        }

        return constraints.get(
            response_type,
            "Provide accurate information based on available data only.",
        )
