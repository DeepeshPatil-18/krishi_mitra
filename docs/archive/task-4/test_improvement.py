#!/usr/bin/env python3
"""Quick test to measure improvement after fixes"""

import sys
import json
sys.path.insert(0, '.')

# Fix encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from scripts.evaluate_farmer_dataset import FarmerQueryEvaluator

print("Running evaluation after deterministic fixes...")
print()

evaluator = FarmerQueryEvaluator('data/evaluation/farmer_queries.jsonl')
evaluator.load_dataset()
evaluator.evaluate_all()
metrics = evaluator.calculate_metrics()

# Load baseline
with open('data/evaluation/task_4_3_baseline.json', 'r', encoding='utf-8') as f:
    baseline = json.load(f)

print("=" * 80)
print("AFTER FIXES METRICS")
print("=" * 80)
print(f"Intent Accuracy:     {metrics['overall_intent_accuracy']*100:.1f}%")
print(f"Entity Accuracy:     {metrics['overall_entity_accuracy']*100:.1f}%")
print(f"Language Accuracy:   {metrics['overall_language_accuracy']*100:.1f}%")
print()

print("COMPARISON TO BASELINE")
print("=" * 80)
intent_change = (metrics['overall_intent_accuracy'] - baseline['overall_metrics']['intent_accuracy']) * 100
entity_change = (metrics['overall_entity_accuracy'] - baseline['overall_metrics']['entity_accuracy']) * 100
lang_change = (metrics['overall_language_accuracy'] - baseline['overall_metrics']['language_accuracy']) * 100

print(f"Intent:  {baseline['overall_metrics']['intent_accuracy']*100:.1f}% -> {metrics['overall_intent_accuracy']*100:.1f}% (Change: {intent_change:+.1f}%)")
print(f"Entity:  {baseline['overall_metrics']['entity_accuracy']*100:.1f}% -> {metrics['overall_entity_accuracy']*100:.1f}% (Change: {entity_change:+.1f}%)")
print(f"Language: {baseline['overall_metrics']['language_accuracy']*100:.1f}% -> {metrics['overall_language_accuracy']*100:.1f}% (Change: {lang_change:+.1f}%)")
print()

print("BY ENTITY TYPE (After Fixes)")
print("=" * 80)
for entity, metrics_entity in metrics.get('entity_metrics', {}).items():
    total = metrics_entity.get('total_expected', 0)
    if total > 0:
        # Use accuracy_when_extracted if available
        accuracy = metrics_entity.get('accuracy_when_extracted', 0) * 100
        print(f"{entity:25} {accuracy:5.1f}% (extracted)")

print()
print("=" * 80)
if entity_change >= 2.0:
    print(f"SUCCESS: Entity accuracy improved by {entity_change:.1f}% (threshold: 2%)")
else:
    print(f"LIMITED IMPROVEMENT: Entity accuracy changed by {entity_change:.1f}% (threshold: 2%)")
print("=" * 80)

# Save results
results = {
    'timestamp': '2026-08-22',
    'phase': 'after_part5_fixes',
    'metrics_after': {
        'intent_accuracy': metrics['overall_intent_accuracy'],
        'entity_accuracy': metrics['overall_entity_accuracy'],
        'language_accuracy': metrics['overall_language_accuracy'],
    },
    'comparison': {
        'intent_change_percent': intent_change,
        'entity_change_percent': entity_change,
        'language_change_percent': lang_change,
    },
    'by_entity_type': metrics.get('entity_metrics', {})
}

with open('data/evaluation/task_4_3_after_fixes.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nResults saved to: data/evaluation/task_4_3_after_fixes.json")
