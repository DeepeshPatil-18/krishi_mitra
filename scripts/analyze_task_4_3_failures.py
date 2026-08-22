#!/usr/bin/env python3
"""
TASK 4.3 PART 3: Failure Taxonomy Analysis
Categorize remaining failures into systematic categories for ROI prioritization
"""

import sys
import json
sys.path.insert(0, '.')

from scripts.evaluate_farmer_dataset import FarmerQueryEvaluator

# Failure categories for classification
FAILURE_CATEGORIES = {
    'parser_bug': 'Extractor fails to detect entity that is present',
    'missing_pattern': 'Normalizer lacks pattern for valid input format',
    'unit_conversion': 'Measurement unit conversion incorrect',
    'language_variation': 'Hindi/Marathi spelling or grammar variation not handled',
    'ambiguous_context': 'Multiple valid interpretations; normalizer guesses wrong',
    'semantic_interpretation': 'Entity value correct but semantic meaning differs',
    'missing_lookup': 'Dictionary/mapping entry missing',
    'tolerance_mismatch': 'Within tolerance but evaluation criteria too strict',
    'incomplete_data': 'User query missing required information',
    'edge_case': 'Rare but valid edge case not covered',
    'false_positive': 'Normalizer extracts something that isn\'t there',
    'malformed_output': 'Normalizer returns wrong type/format'
}

print("="*80)
print("TASK 4.3 PART 3: FAILURE TAXONOMY ANALYSIS")
print("="*80)
print()

# Load baseline
with open('data/evaluation/task_4_3_baseline.json', 'r', encoding='utf-8') as f:
    baseline = json.load(f)

print("BASELINE SUMMARY:")
print(f"  Intent Accuracy: {baseline['overall_metrics']['intent_accuracy']*100:.1f}%")
print(f"  Entity Accuracy: {baseline['overall_metrics']['entity_accuracy']*100:.1f}%")
print(f"  Language Accuracy: {baseline['overall_metrics']['language_accuracy']*100:.1f}%")
print()

# Run evaluator to get detailed failure data
print("Running detailed evaluation to collect failure data...")
evaluator = FarmerQueryEvaluator('data/evaluation/farmer_queries.jsonl')
evaluator.load_dataset()
evaluator.evaluate_all()
metrics = evaluator.calculate_metrics()

# Collect failures by entity type
failures_by_entity = {}
for result in evaluator.results:
    if not result['entity_match']:
        for entity_type in result['expected_entities']:
            if entity_type not in failures_by_entity:
                failures_by_entity[entity_type] = []
            
            expected = result['expected_entities'].get(entity_type)
            predicted = result['predicted_entities'].get(entity_type)
            
            failure_info = {
                'message': result['message'],
                'language': result['language'],
                'intent': result['intent'],
                'expected': expected,
                'predicted': predicted,
                'difficulty': result.get('difficulty', 'unknown'),
                'category': 'unclassified'  # To be filled manually
            }
            failures_by_entity[entity_type].append(failure_info)

# Print failure summary by entity
print("\nFAILURES BY ENTITY TYPE:")
print("-" * 80)
for entity_type, failures in sorted(failures_by_entity.items()):
    print(f"\n{entity_type.upper()}: {len(failures)} failures")
    
    # Sample first 3 failures for each type
    for i, failure in enumerate(failures[:3]):
        print(f"\n  [{i+1}] Message: {failure['message'][:80]}...")
        print(f"      Language: {failure['language']}, Intent: {failure['intent']}")
        print(f"      Expected: {failure['expected']}")
        print(f"      Predicted: {failure['predicted']}")
        print(f"      Difficulty: {failure['difficulty']}")

# Print failure categories guide
print("\n\n" + "="*80)
print("FAILURE CATEGORIES (for manual classification):")
print("="*80)
for idx, (cat_key, cat_desc) in enumerate(FAILURE_CATEGORIES.items(), 1):
    print(f"{idx:2}. {cat_key:20} - {cat_desc}")

print("\n\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("1. Review failure samples above")
print("2. Categorize failures using the categories list")
print("3. Create frequency × impact ÷ complexity table for ROI prioritization")
print("4. Implement only highest-ROI deterministic fixes")
print("="*80)

# Save failure data for further analysis
failure_data = {
    'timestamp': '2026-08-22',
    'failures_by_entity_type': {
        entity: {
            'count': len(failures),
            'samples': failures[:5]  # Keep first 5 samples
        }
        for entity, failures in failures_by_entity.items()
    },
    'failure_categories': FAILURE_CATEGORIES
}

with open('data/evaluation/task_4_3_failures_raw.json', 'w', encoding='utf-8') as f:
    json.dump(failure_data, f, ensure_ascii=False, indent=2)

print("\nFailure data saved to: data/evaluation/task_4_3_failures_raw.json")
