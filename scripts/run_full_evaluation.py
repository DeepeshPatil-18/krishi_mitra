#!/usr/bin/env python3
"""
Full evaluation runner that saves ALL query results (not just first 10).
Used for TASK 4.5 failure audit.
"""

import sys, os, json, logging
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

logging.basicConfig(level=logging.WARNING)   # suppress INFO noise to stdout

from scripts.evaluate_farmer_dataset import FarmerQueryEvaluator

OUTPUT_PATH = "data/evaluation/task_4_5_full_results.json"

def main():
    evaluator = FarmerQueryEvaluator("data/evaluation/farmer_queries.jsonl")
    evaluator.load_dataset()
    evaluator.evaluate_all()
    evaluator.calculate_metrics()

    # Save ALL results
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "metrics": evaluator.metrics,
            "results": evaluator.results   # ALL 60
        }, f, indent=2, ensure_ascii=False)

    m = evaluator.metrics
    print(f"Dataset: {m['dataset_size']} queries")
    print(f"Intent:   {100*m['overall_intent_accuracy']:.1f}%")
    print(f"Entity:   {100*m['overall_entity_accuracy']:.1f}%")
    print(f"Language: {100*m['overall_language_accuracy']:.1f}%")
    print(f"Capability: {100*m['overall_capability_accuracy']:.1f}%")
    print()
    print("Per-entity:")
    for etype, stats in m['entity_metrics'].items():
        acc = stats['accuracy_when_extracted']
        total = stats['total_expected']
        print(f"  {etype}: {100*acc:.1f}%  ({total} cases)")
    print()
    print(f"Full results saved to: {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
