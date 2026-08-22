"""Domain constants for KrishiMitra"""

# Supported Languages
SUPPORTED_LANGUAGES = ["marathi", "hindi", "english"]

# Allied Enterprises
ALLIED_ENTERPRISES = {
    "apiculture": {
        "name_en": "Beekeeping",
        "name_hi": "मधुमक्खी पालन",
        "name_mr": "मधुमक्खी पालन",
    },
    "poultry": {
        "name_en": "Poultry Farming",
        "name_hi": "कुक्कुट पालन",
        "name_mr": "मुर्गीपालन",
    },
    "fisheries": {
        "name_en": "Fisheries",
        "name_hi": "मत्स्य पालन",
        "name_mr": "मासेमारी",
    },
    "goat_farming": {
        "name_en": "Goat Farming",
        "name_hi": "बकरी पालन",
        "name_mr": "शेळीपालन",
    },
    "mushroom": {
        "name_en": "Mushroom Cultivation",
        "name_hi": "मशरूम खेती",
        "name_mr": "मशरूम शेती",
    },
    "vermicomposting": {
        "name_en": "Vermicomposting",
        "name_hi": "वर्मीकम्पोस्टिंग",
        "name_mr": "वर्मीकम्पोस्टिंग",
    },
}

# Intent Types
INTENT_TYPES = {
    "livelihood_recommendation": "Get enterprise recommendations based on farmer context",
    "scheme_search": "Find relevant government schemes",
    "training_request": "Get training material and guidance",
    "market_search": "Find buyers or market information",
    "expert_request": "Request expert assistance",
    "general_question": "General agricultural question",
    "community": "Access community posts/discussions",
}

# States (India)
INDIAN_STATES = [
    "andhra_pradesh",
    "arunachal_pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal_pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya_pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil_nadu",
    "telangana",
    "tripura",
    "uttar_pradesh",
    "uttarakhand",
    "west_bengal",
]

# Expert Categories
EXPERT_CATEGORIES = [
    "enterprise_setup",
    "disease_management",
    "resource_planning",
    "market_access",
    "financial_planning",
    "scheme_application",
    "training_guidance",
    "other",
]

# Suitability Scoring Thresholds
MIN_SUITABILITY_SCORE = 0.0
MAX_SUITABILITY_SCORE = 100.0
MINIMUM_VIABLE_SCORE = 50.0

# HTTP Status Messages
HTTP_MESSAGES = {
    200: "Success",
    400: "Bad Request",
    404: "Not Found",
    500: "Internal Server Error",
}
