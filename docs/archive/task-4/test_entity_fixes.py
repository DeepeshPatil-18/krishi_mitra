#!/usr/bin/env python3
"""Test the deterministic fixes for Part 5"""

import sys
sys.path.insert(0, '.')

# Fix Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.entity_normalizer import EntityNormalizer

print("="*80)
print("TESTING DETERMINISTIC FIXES (PART 5)")
print("="*80)
print()

# TEST 1: Land size fixes
print("\n#1: LAND SIZE CONVERSIONS (ROI=175)")
print("-"*80)

test_cases_land = [
    ("1 एकर", 0.404686),
    ("2 एकर", 0.809372),
    ("1.5 एकर", 0.607029),
    ("0.5 एकर", 0.202343),
    ("1 hectare", 1.0),
    ("2 hectare", 2.0),
    ("1.5 hectares", 1.5),
    ("आधा एकर", 0.202343),
    ("डेढ़ एकर", 0.607029),
]

for test_input, expected in test_cases_land:
    result = EntityNormalizer.normalize_land_size(test_input)
    if result:
        actual, unit_type = result
        error = abs(actual - expected) / expected * 100
        status = "✓" if error < 1 else "✗"
        print(f"  {status} '{test_input}' → {actual:.3f} ha (expect {expected:.3f}, error {error:.1f}%)")
    else:
        print(f"  ✗ '{test_input}' → FAILED TO PARSE")

print()

# TEST 2: Budget ranges
print("\n#2: BUDGET RANGES (ROI=100)")
print("-"*80)

test_cases_budget = [
    ("50000 to 100000", 75000),
    ("50-100k", 75000),
    ("around 50000", 50000),
    ("लगभग 50000", 50000),
    ("50000", 50000),
    ("50 हजार", 50000),
]

for test_input, expected in test_cases_budget:
    result = EntityNormalizer.normalize_number(test_input)
    if result:
        actual, fmt = result
        # For ranges, allow wider tolerance
        error = abs(actual - expected) / expected * 100
        status = "✓" if error <= 5 else "✗"
        print(f"  {status} '{test_input}' → {actual:.0f} (expect {expected:.0f}, error {error:.1f}%, format: {fmt})")
    else:
        print(f"  ✗ '{test_input}' → FAILED TO PARSE")

print()

# TEST 3: Experience level
print("\n#3: EXPERIENCE LEVEL (ROI=40)")
print("-"*80)

test_cases_exp = [
    ("नया", "beginner"),
    ("beginner", "beginner"),
    ("1 year", "beginner"),
    ("2 years", "intermediate"),
    ("5 years", "intermediate"),
    ("10 years", "intermediate"),
    ("15 years", "expert"),
    ("expert", "expert"),
    ("विशेषज्ञ", "expert"),
    ("अनुभवी किसान", "intermediate"),
]

for test_input, expected in test_cases_exp:
    result = EntityNormalizer.normalize_experience_level(test_input)
    if result:
        actual, fmt = result
        status = "✓" if actual == expected else "✗"
        print(f"  {status} '{test_input}' → {actual} (expect {expected}, format: {fmt})")
    else:
        print(f"  ✗ '{test_input}' → FAILED TO PARSE (expected {expected})")

print()
print("="*80)
print("Tests complete!")
print("="*80)
