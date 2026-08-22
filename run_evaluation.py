#!/usr/bin/env python3
"""Run evaluation and compare with baseline"""

import sys
import json
sys.path.insert(0, '.')

from scripts.evaluate_farmer_dataset import FarmerQueryEvaluator

print("="*80)
print("TASK 4.1 EVALUATION - DETERMINISTIC REPAIR")
print("="*80)
print()

# Run evaluation
evaluator = FarmerQueryEvaluator('data/evaluation/farmer_queries.jsonl')
evaluator.load_dataset()
evaluator.evaluate_all()
metrics = evaluator.calculate_metrics()

# Print summary
print("AFTER REPAIRS - METRICS:")
print(f"  Intent Accuracy:             {metrics['overall_intent_accuracy']:.1%}")
print(f"  Entity Accuracy:             {metrics['overall_entity_accuracy']:.1%}")
print(f"  Language Accuracy:           {metrics['overall_language_accuracy']:.1%}")
print(f"  Capability Routing:          {metrics['overall_capability_accuracy']:.1%}")

print("\nBY LANGUAGE:")
for lang in ['marathi', 'hindi', 'english']:
    if lang in metrics['by_language']:
        lang_data = metrics['by_language'][lang]
        print(f"  {lang.upper():10}: Intent {lang_data['intent_accuracy']:.1%}, Entity {lang_data['entity_accuracy']:.1%}")

print("\nBY INTENT:")
for intent, data in metrics['by_intent'].items():
    print(f"  {intent:30}: {data['accuracy']:.1%}")

print("\nBY DIFFICULTY:")
for diff in ['easy', 'medium', 'hard']:
    if diff in metrics['by_difficulty']:
        diff_data = metrics['by_difficulty'][diff]
        print(f"  {diff.upper():10}: Intent {diff_data['intent_accuracy']:.1%}")

print("\nENTITY METRICS:")
for entity, data in metrics['entity_metrics'].items():
    print(f"  {entity:30}: extraction={data['extraction_rate']:.1%}, accuracy={data['accuracy_when_extracted']:.1%}")

print("\n" + "="*80)
print("BEFORE vs AFTER COMPARISON")
print("="*80)

baseline_metrics = {
    "overall_intent_accuracy": 0.4666666666666667,
    "overall_entity_accuracy": 0.0,
    "overall_language_accuracy": 1.0,
    "overall_capability_accuracy": 0.4166666666666667,
}

print("\nOVERALL METRICS:")
print(f"  Intent Accuracy:      {baseline_metrics['overall_intent_accuracy']:.1%} → {metrics['overall_intent_accuracy']:.1%} ({metrics['overall_intent_accuracy'] - baseline_metrics['overall_intent_accuracy']:+.1%})")
print(f"  Entity Accuracy:      {baseline_metrics['overall_entity_accuracy']:.1%} → {metrics['overall_entity_accuracy']:.1%} ({metrics['overall_entity_accuracy'] - baseline_metrics['overall_entity_accuracy']:+.1%})")
print(f"  Language Accuracy:    {baseline_metrics['overall_language_accuracy']:.1%} → {metrics['overall_language_accuracy']:.1%} ({metrics['overall_language_accuracy'] - baseline_metrics['overall_language_accuracy']:+.1%})")
print(f"  Capability Routing:   {baseline_metrics['overall_capability_accuracy']:.1%} → {metrics['overall_capability_accuracy']:.1%} ({metrics['overall_capability_accuracy'] - baseline_metrics['overall_capability_accuracy']:+.1%})")

# Save new results
with open('data/evaluation/task_4_1_results.json', 'w', encoding='utf-8') as f:
    json.dump({'metrics': metrics, 'results': evaluator.results}, f, ensure_ascii=False, indent=2)

print("\nResults saved to: data/evaluation/task_4_1_results.json")
print("="*80)
