#!/usr/bin/env python3
"""TASK 4.2 Final Evaluation - Run TASK 4 dataset through normalizer and measure improvements"""

import sys
import json
sys.path.insert(0, '.')

from app.services.entity_extractor import EntityExtractor
from app.services.entity_normalizer import EntityNormalizer
from app.services.language_service import LanguageService
from app.services.intent_router import IntentRouter
import logging

logging.basicConfig(level=logging.WARNING)

print("="*80)
print("TASK 4.2 FINAL EVALUATION - DETERMINISTIC NORMALIZATION")
print("="*80)
print()

# Load TASK 4 evaluation dataset
test_queries = []
with open('data/evaluation/farmer_queries.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            test_queries.append(json.loads(line))

print(f"Loaded {len(test_queries)} queries from TASK 4 dataset")
print()

# Prepare language service
lang_service = LanguageService()

# Results tracking
results = []
intent_correct = 0
entity_correct = 0
language_correct = 0

by_entity_type = {}

for query in test_queries:
    query_id = query.get('id')
    message = query['message']
    expected_intent = query.get('expected_intent')
    expected_entities = query.get('expected_entities', {})
    expected_language = query.get('language', 'unknown')
    
    # Detect language
    detected_language = lang_service.detect_language(message)
    language_match = detected_language.lower() == expected_language.lower()
    if language_match:
        language_correct += 1
    
    # Detect intent
    detected_intent, confidence, _ = IntentRouter.detect_intent(message, language=detected_language)
    intent_match = detected_intent.value == expected_intent
    if intent_match:
        intent_correct += 1
    
    # Extract and normalize entities
    extracted_raw = EntityExtractor.extract_all(message, language=detected_language)
    
    # Apply normalization
    entity_matches = {}
    all_entities_match = True
    
    for entity_type, expected_value in expected_entities.items():
        raw_value = extracted_raw.get(entity_type)
        
        # Normalize
        normalization_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
        predicted_value = normalization_result.get('normalized_value')
        
        # Compare
        if entity_type == 'land_size_hectares':
            # Allow 5% tolerance
            if expected_value and predicted_value:
                tolerance = abs(expected_value) * 0.05
                match = abs(expected_value - predicted_value) <= tolerance
            else:
                match = expected_value == predicted_value
        else:
            # Exact match
            if isinstance(predicted_value, str) and isinstance(expected_value, str):
                match = predicted_value.lower() == expected_value.lower()
            else:
                match = expected_value == predicted_value
        
        entity_matches[entity_type] = {
            'expected': expected_value,
            'predicted': predicted_value,
            'match': match,
            'confidence': normalization_result.get('normalization_confidence', 0.0)
        }
        
        if not match:
            all_entities_match = False
        
        # Track by entity type
        if entity_type not in by_entity_type:
            by_entity_type[entity_type] = {'correct': 0, 'total': 0}
        by_entity_type[entity_type]['total'] += 1
        if match:
            by_entity_type[entity_type]['correct'] += 1
    
    if all_entities_match and expected_entities:
        entity_correct += 1
    
    results.append({
        'id': query_id,
        'language_match': language_match,
        'intent_match': intent_match,
        'entity_matches': entity_matches,
        'all_entities_match': all_entities_match
    })

# Calculate metrics
total_queries = len(test_queries)
queries_with_entities = sum(1 for q in test_queries if q.get('expected_entities'))

print("="*80)
print("TASK 4.2 EVALUATION RESULTS")
print("="*80)
print()

print("LANGUAGE DETECTION:")
print(f"  Correct: {language_correct}/{total_queries} ({language_correct/total_queries*100:.1f}%)")
print()

print("INTENT DETECTION:")
print(f"  Correct: {intent_correct}/{total_queries} ({intent_correct/total_queries*100:.1f}%)")
print()

print("ENTITY EXTRACTION + NORMALIZATION:")
print(f"  Correct: {entity_correct}/{queries_with_entities} ({entity_correct/queries_with_entities*100:.1f}% of queries with entities)")
print()

print("BY ENTITY TYPE:")
for entity_type in sorted(by_entity_type.keys()):
    stats = by_entity_type[entity_type]
    accuracy = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
    print(f"  {entity_type}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
print()

# Compare to TASK 4.1 baseline
print("="*80)
print("COMPARISON: TASK 4 → TASK 4.1 → TASK 4.2")
print("="*80)
print()

print("INTENT ACCURACY:")
print(f"  TASK 4.0 baseline:     46.7%")
print(f"  TASK 4.1 after repairs: 61.7%")
print(f"  TASK 4.2 (normalizer):  {intent_correct/total_queries*100:.1f}%")
print()

print("ENTITY ACCURACY:")
print(f"  TASK 4.0 baseline:     0.0%")
print(f"  TASK 4.1 after repairs: 0.0% (blocked on parsing)")
print(f"  TASK 4.2 (normalizer):  {entity_correct/queries_with_entities*100:.1f}%")
print()

# Save results
task_4_2_results = {
    'timestamp': '2026-08-21',
    'dataset_size': total_queries,
    'metrics': {
        'language_accuracy': language_correct / total_queries,
        'intent_accuracy': intent_correct / total_queries,
        'entity_accuracy': entity_correct / queries_with_entities if queries_with_entities > 0 else 0.0
    },
    'by_entity_type': {
        k: v['correct'] / v['total'] if v['total'] > 0 else 0
        for k, v in by_entity_type.items()
    },
    'comparison': {
        'task_4_0_intent': 0.4666666666666667,
        'task_4_1_intent': 0.6166666666666667,
        'task_4_2_intent': intent_correct / total_queries,
        'task_4_0_entity': 0.0,
        'task_4_1_entity': 0.0,
        'task_4_2_entity': entity_correct / queries_with_entities if queries_with_entities > 0 else 0.0
    }
}

with open('data/evaluation/task_4_2_evaluation.json', 'w', encoding='utf-8') as f:
    json.dump(task_4_2_results, f, ensure_ascii=False, indent=2)

print("Results saved to: data/evaluation/task_4_2_evaluation.json")
