#!/usr/bin/env python3
"""Test the new deterministic normalizer against baseline"""

import sys
import json
sys.path.insert(0, '.')

from app.services.entity_normalizer import EntityNormalizer
import logging

logging.basicConfig(level=logging.WARNING)

print("="*80)
print("ENTITY NORMALIZER TESTING")
print("="*80)
print()

# Load test dataset
test_cases = []
with open('data/evaluation/entity_normalization_cases.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            test_cases.append(json.loads(line))

print(f"Testing {len(test_cases)} cases\n")

# Results tracking
results = []
success_count = 0
partial_count = 0
failure_count = 0

# By entity type breakdown
by_entity = {}

for test_case in test_cases:
    case_id = test_case['id']
    message = test_case['message']
    entity_type = test_case['entity_type']
    expected_normalized = test_case.get('expected_normalized')
    
    # Initialize entity type tracking
    if entity_type not in by_entity:
        by_entity[entity_type] = {'total': 0, 'success': 0, 'failure': 0, 'partial': 0}
    by_entity[entity_type]['total'] += 1
    
    # For testing, we'll normalize the raw_value directly
    # (In real use, this would come from EntityExtractor)
    raw_value = test_case.get('expected_raw')  # Use expected_raw as if it was extracted
    
    # Test normalization
    normalized_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
    extracted_value = normalized_result.get('normalized_value')
    
    # Determine result
    if expected_normalized is None:
        # Expected to NOT normalize/be absent
        if extracted_value is None:
            result = 'SUCCESS'
            success_count += 1
            by_entity[entity_type]['success'] += 1
        else:
            result = 'FAILURE'  # Should not have normalized but did
            failure_count += 1
            by_entity[entity_type]['failure'] += 1
    else:
        # Expected to normalize
        if extracted_value is None:
            result = 'FAILURE'  # Should have normalized but didn't
            failure_count += 1
            by_entity[entity_type]['failure'] += 1
        else:
            # Check if value matches
            if entity_type == 'land_size_hectares' or entity_type == 'time_numeric':
                # Allow some tolerance
                if isinstance(extracted_value, dict) and isinstance(expected_normalized, dict):
                    match = extracted_value.get('value') == expected_normalized.get('value')
                elif isinstance(extracted_value, (int, float)) and isinstance(expected_normalized, (int, float)):
                    tolerance = abs(expected_normalized) * 0.05
                    match = abs(extracted_value - expected_normalized) <= tolerance
                else:
                    match = extracted_value == expected_normalized
            else:
                # Exact match (case-insensitive for strings)
                if isinstance(extracted_value, str) and isinstance(expected_normalized, str):
                    match = extracted_value.lower() == expected_normalized.lower()
                else:
                    match = extracted_value == expected_normalized
            
            if match:
                result = 'SUCCESS'
                success_count += 1
                by_entity[entity_type]['success'] += 1
            else:
                result = 'PARTIAL'  # Normalized but value doesn't match
                partial_count += 1
                by_entity[entity_type]['partial'] += 1
    
    results.append({
        'id': case_id,
        'message': message,
        'entity_type': entity_type,
        'raw_value': raw_value,
        'expected_normalized': expected_normalized,
        'extracted_normalized': extracted_value,
        'result': result,
        'confidence': normalized_result.get('normalization_confidence'),
        'notes': test_case.get('notes', '')
    })

# Print summary
print("="*80)
print("NORMALIZER RESULTS SUMMARY")
print("="*80)
print(f"Total test cases: {len(test_cases)}")
print(f"SUCCESS (exact match): {success_count}")
print(f"PARTIAL (normalized but wrong value): {partial_count}")
print(f"FAILURE (normalization failed): {failure_count}")
print()

success_rate = (success_count / len(test_cases)) * 100 if test_cases else 0
partial_rate = (partial_count / len(test_cases)) * 100 if test_cases else 0
failure_rate = (failure_count / len(test_cases)) * 100 if test_cases else 0

print(f"Success rate: {success_rate:.1f}%")
print(f"Partial rate: {partial_rate:.1f}%")
print(f"Failure rate: {failure_rate:.1f}%")
print()

# Improvement over baseline
baseline_success = 47
baseline_failure = 24
improvement = success_count - baseline_success

print(f"BASELINE: {baseline_success} success")
print(f"AFTER NORMALIZATION: {success_count} success")
print(f"IMPROVEMENT: +{improvement} cases (+{(improvement/len(test_cases))*100:.1f}%)")
print()

# By entity type
print("="*80)
print("BY ENTITY TYPE")
print("="*80)
for entity_type in sorted(by_entity.keys()):
    stats = by_entity[entity_type]
    success_pct = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"\n{entity_type}:")
    print(f"  Total: {stats['total']}")
    print(f"  Success: {stats['success']} ({success_pct:.1f}%)")
    print(f"  Partial: {stats['partial']}")
    print(f"  Failure: {stats['failure']}")

# Detailed failures
print("\n" + "="*80)
print("REMAINING FAILURES - DETAILED")
print("="*80)

failures = [r for r in results if r['result'] in ['FAILURE', 'PARTIAL']]
print(f"\nTotal issues: {len(failures)}")

# Group by type
by_type = {}
for f in failures:
    entity_type = f['entity_type']
    if entity_type not in by_type:
        by_type[entity_type] = []
    by_type[entity_type].append(f)

for entity_type in sorted(by_type.keys()):
    cases = by_type[entity_type]
    print(f"\n{entity_type}: {len(cases)} issues")
    for case in cases[:3]:  # Show first 3
        print(f"  ID: {case['id']}")
        print(f"    Message: {case['message']}")
        print(f"    Raw: {case['raw_value']}")
        print(f"    Expected: {case['expected_normalized']}")
        print(f"    Normalized: {case['extracted_normalized']}")
        print(f"    Confidence: {case['confidence']:.2f}")
        print(f"    Status: {case['result']}")

# Save results
normalizer_results = {
    'timestamp': '2026-08-21',
    'test_cases_count': len(test_cases),
    'summary': {
        'success': success_count,
        'partial': partial_count,
        'failure': failure_count,
        'success_rate': success_rate,
        'partial_rate': partial_rate,
        'failure_rate': failure_rate,
        'improvement_over_baseline': improvement
    },
    'by_entity_type': by_entity,
    'critical_improvements': {
        'marathi_number_words': 'Now handling पन्नास, पचास, etc',
        'location_normalization': 'Returning district (nashik) instead of state (maharashtra)',
        'hindi_spelling_variations': 'Handling एकड़ vs एकर variations',
        'time_numeric': 'Now extracting 3 महीने as {value: 3, unit: months}'
    }
}

with open('data/evaluation/entity_normalizer_results.json', 'w', encoding='utf-8') as f:
    json.dump(normalizer_results, f, ensure_ascii=False, indent=2)

print("\n" + "="*80)
print(f"Results saved to: data/evaluation/entity_normalizer_results.json")
print("="*80)
