#!/usr/bin/env python3
"""Create TASK 4.3 baseline - record current state before modifications"""

import sys
import json
sys.path.insert(0, '.')

from scripts.evaluate_farmer_dataset import FarmerQueryEvaluator

print("="*80)
print("TASK 4.3 BASELINE CREATION")
print("="*80)
print()

# Run full evaluation
evaluator = FarmerQueryEvaluator('data/evaluation/farmer_queries.jsonl')
evaluator.load_dataset()
evaluator.evaluate_all()
results = evaluator.calculate_metrics()

# Extract key metrics
print("BASELINE METRICS:")
print(f"  Intent Accuracy: {results['intent_accuracy']*100:.1f}%")
print(f"  Entity Accuracy: {results['entity_accuracy']*100:.1f}%")
print(f"  Language Accuracy: {results['language_accuracy']*100:.1f}%")
print(f"  Capability Routing: {results['capability_accuracy']*100:.1f}%")
print()

print("BY LANGUAGE:")
for lang, metrics in results['by_language'].items():
    intent_acc = metrics['intent_accuracy'] if 'intent_accuracy' in metrics else 0
    entity_acc = metrics['entity_accuracy'] if 'entity_accuracy' in metrics else 0
    print(f"  {lang}: intent={intent_acc*100:.1f}%, entity={entity_acc*100:.1f}%")
print()

print("BY INTENT:")
for intent, metrics in results['by_intent'].items():
    acc = metrics['accuracy'] if 'accuracy' in metrics else 0
    print(f"  {intent}: {acc*100:.1f}%")
print()

print("BY ENTITY TYPE:")
for entity, metrics in results['entity_metrics'].items():
    if 'accuracy' in metrics and metrics.get('total', 0) > 0:
        print(f"  {entity}: {metrics['accuracy']*100:.1f}% ({metrics.get('correct', 0)}/{metrics.get('total', 0)})")
print()

# Save baseline
baseline = {
    'timestamp': '2026-08-22',
    'baseline_from_task': '4.2',
    'overall_metrics': {
        'intent_accuracy': results['intent_accuracy'],
        'entity_accuracy': results['entity_accuracy'],
        'language_accuracy': results['language_accuracy'],
        'capability_accuracy': results['capability_accuracy'],
        'total_queries': len(evaluator.results) if hasattr(evaluator, 'results') else 60,
        'test_pass_rate': 0.923  # From TASK 4.2
    },
    'by_language': results.get('by_language', {}),
    'by_intent': results.get('by_intent', {}),
    'by_entity_type': results.get('entity_metrics', {}),
    'by_difficulty': results.get('by_difficulty', {}),
}

with open('data/evaluation/task_4_3_baseline.json', 'w', encoding='utf-8') as f:
    json.dump(baseline, f, ensure_ascii=False, indent=2)

print("="*80)
print("Baseline saved to: data/evaluation/task_4_3_baseline.json")
print("="*80)
