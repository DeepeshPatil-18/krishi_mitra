"""Debug EntityExtractor vs EntityNormalizer"""

from app.services.entity_extractor import EntityExtractor
from app.services.entity_normalizer import EntityNormalizer

test_cases = [
    ("2 एकर जमीन", "marathi"),
    ("आधा एकर", "marathi"),
    ("डेढ़ एकर", "hindi"),
    ("50 हजार रुपये", "hindi"),
    ("लगभग 50000", "hindi"),
    ("50-100k budget", "english"),
    ("2 acres", "english"),
    ("1 year experience", "english"),
    ("5 years experience", "english"),
]

for message, lang in test_cases:
    print("=" * 80)
    print(f"Message: '{message}' ({lang})")
    print("-" * 80)
    
    # EntityExtractor
    raw = EntityExtractor.extract_all(message, lang)
    print(f"EntityExtractor: {raw}")
    
    # Try EntityNormalizer on raw strings from message
    # Land size
    if "एकर" in message or "acre" in message:
        land_raw = message.split()[0] if " " in message else message
        norm = EntityNormalizer.normalize_land_size(message)
        print(f"EntityNormalizer.normalize_land_size('{message}'): {norm}")
    
    # Budget
    if "हजार" in message or "rupees" in message or "रुपये" in message or "budget" in message or "k" in message:
        norm = EntityNormalizer.normalize_number(message)
        print(f"EntityNormalizer.normalize_number('{message}'): {norm}")
    
    # Experience
    if "experience" in message or "year" in message:
        norm = EntityNormalizer.normalize_experience_level(message)
        print(f"EntityNormalizer.normalize_experience_level('{message}'): {norm}")
    
    print()
