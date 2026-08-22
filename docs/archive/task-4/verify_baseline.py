#!/usr/bin/env python3
"""Verify TASK 4 baseline is reproducible"""

import sys
import json
sys.path.insert(0, '.')

from scripts.evaluate_farmer_dataset import FarmerQueryEvaluator

print("=" * 80)
print("VERIFYING TASK 4 BASELINE")
print("=" * 80)

# Run evaluation
evaluator = FarmerQueryEvaluator('data/evaluation/farmer_queries.jsonl')
evaluator.load_dataset()
evaluator.evaluate_all()
results_list = evaluator.calculate_metrics()
results = {'metrics': evaluator.metrics, 'results': evaluator.results}

# Extract metrics
metrics = results['metrics']

print("\nBASELINE METRICS (REPRODUCED):")
print(f"  Intent Accuracy:             {metrics['overall_intent_accuracy']:.1%}")
print(f"  Entity Accuracy:             {metrics['overall_entity_accuracy']:.1%}")
print(f"  Language Accuracy:           {metrics['overall_language_accuracy']:.1%}")
print(f"  Capability Routing:          {metrics['overall_capability_accuracy']:.1%}")

print("\nBY LANGUAGE:")
for lang in ['marathi', 'hindi', 'english']:
    lang_data = metrics['by_language'][lang]
    print(f"  {lang.upper():10}: Intent {lang_data['intent_accuracy']:.1%}, Entity {lang_data['entity_accuracy']:.1%}")

print("\nBY INTENT:")
for intent, data in metrics['by_intent'].items():
    print(f"  {intent:30}: {data['accuracy']:.1%}")

print("\nBY DIFFICULTY:")
for diff in ['easy', 'medium', 'hard']:
    diff_data = metrics['by_difficulty'][diff]
    print(f"  {diff.upper():10}: Intent {diff_data['intent_accuracy']:.1%}")

print("\nENTITY METRICS:")
for entity, data in metrics['entity_metrics'].items():
    print(f"  {entity:30}: extraction_rate={data['extraction_rate']:.1%}, accuracy={data['accuracy_when_extracted']:.1%}")

print("\n" + "=" * 80)
print("BASELINE VERIFICATION COMPLETE")
print("=" * 80)

# Now check some actual results to understand extraction
print("\nSAMPLE EXTRACTIONS (first 3 results):")
for result in results['results'][:3]:
    print(f"\nExample: {result['id']}")
    print(f"  Message: {result['message'][:60]}...")
    print(f"  Expected: {result['expected_entities']}")
    print(f"  Predicted: {result['predicted_entities']}")
    print(f"  Intent - Expected: {result['expected_intent']}, Got: {result['predicted_intent']}")
