#!/usr/bin/env python3
"""Test entity extraction directly"""

import sys
sys.path.insert(0, '.')

from app.services.entity_extractor import EntityExtractor

print("Testing EntityExtractor directly\n")

# Test cases from evaluation dataset
test_cases = [
    ("50000 रुपये आणि 2 एकर जमीन", "marathi"),
    ("50 हजार रुपये", "marathi"),  
    ("2 एकर", "marathi"),
    ("नाशिकमध्ये", "marathi"),
    ("मशरूम", "marathi"),
    ("मेरे पास 30000 रुपये हैं", "hindi"),
    ("I have 50000 rupees", "english"),
]

for text, lang in test_cases:
    try:
        result = EntityExtractor.extract_all(text, lang)
        print(f"Text: {text}")
        print(f"Language: {lang}")
        print(f"Extracted: {result}")
        print()
    except Exception as e:
        print(f"ERROR with text '{text}': {e}")
        print()

