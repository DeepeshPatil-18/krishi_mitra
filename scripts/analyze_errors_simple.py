#!/usr/bin/env python3
"""
Simplified error analysis - focuses on patterns without printing unicode.
"""

import json
import sys
import os
from collections import defaultdict

# Add workspace root to path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)


def analyze_errors():
    """Analyze failures from evaluation results"""
    
    # Load results
    results_file = os.path.join(workspace_root, "data/evaluation/results.json")
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = data["results"]
    
    # Collect failures by category
    intent_failures_by_category = defaultdict(lambda: {"total": 0, "failures": 0})
    entity_failures = defaultdict(int)
    intent_confusion_matrix = defaultdict(lambda: defaultdict(int))
    
    print("=" * 80)
    print("ERROR ANALYSIS - TASK 4 BASELINE EVALUATION")
    print("=" * 80)
    print()
    
    # Categorize results
    for result in results:
        expected_intent = result["expected_intent"]
        predicted_intent = result["predicted_intent"]
        language = result["language"]
        difficulty = result["difficulty"]
        
        # Track by category
        category = f"{language}_{difficulty}"
        intent_failures_by_category[category]["total"] += 1
        
        if expected_intent != predicted_intent:
            intent_failures_by_category[category]["failures"] += 1
            intent_confusion_matrix[expected_intent][predicted_intent] += 1
        
        # Track entity extraction
        for entity_type, matches_info in result["entity_matches"].items():
            if not matches_info.get("match", False):
                expected_val = matches_info.get("expected")
                predicted_val = matches_info.get("predicted")
                
                if predicted_val is None:
                    entity_failures[f"{entity_type}_NOT_EXTRACTED"] += 1
                else:
                    entity_failures[f"{entity_type}_WRONG_VALUE"] += 1
    
    # Print intent confusion matrix
    print("INTENT CONFUSION MATRIX")
    print("-" * 80)
    all_intents = sorted(set(intent_confusion_matrix.keys()) | set(
        i for d in intent_confusion_matrix.values() for i in d.keys()
    ))
    
    print(f"{'Expected':<30}", end="")
    for intent in all_intents:
        print(f"{intent[:20]:<20}", end="")
    print()
    print("-" * 80)
    
    for expected in all_intents:
        print(f"{expected:<30}", end="")
        for predicted in all_intents:
            count = intent_confusion_matrix[expected][predicted]
            if expected == predicted:
                print(f"[{count:>2}] CORRECT ", end="")
            else:
                if count > 0:
                    print(f" {count:>2}  ERROR   ", end="")
                else:
                    print(f" -            ", end="")
        print()
    
    print()
    print("INTENT FAILURE ANALYSIS BY CATEGORY")
    print("-" * 80)
    
    for category in sorted(intent_failures_by_category.keys()):
        stats = intent_failures_by_category[category]
        total = stats["total"]
        failures = stats["failures"]
        error_rate = (failures / total * 100) if total > 0 else 0
        print(f"{category:30}: {failures:2}/{total:2} failures ({error_rate:5.1f}%)")
    
    print()
    print("ENTITY EXTRACTION ISSUES")
    print("-" * 80)
    print("Note: 100% extraction rate but 0-12.5% accuracy means entities are extracted")
    print("      but have WRONG VALUES or WRONG TYPES. This is NOT a data retrieval")
    print("      problem, it's a VALUE EXTRACTION/PARSING problem.")
    print()
    
    not_extracted = sorted([k for k in entity_failures.keys() if "NOT_EXTRACTED" in k],
                           key=lambda x: entity_failures[x], reverse=True)
    wrong_values = sorted([k for k in entity_failures.keys() if "WRONG_VALUE" in k],
                          key=lambda x: entity_failures[x], reverse=True)
    
    if not_extracted:
        print("ENTITIES NOT EXTRACTED:")
        for entity_type in not_extracted:
            count = entity_failures[entity_type]
            print(f"  {entity_type}: {count} failures")
    
    if wrong_values:
        print()
        print("ENTITIES EXTRACTED BUT WITH WRONG VALUES:")
        for entity_type in wrong_values:
            count = entity_failures[entity_type]
            print(f"  {entity_type}: {count} failures")
    
    print()
    print("=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print()
    
    # Calculate key metrics
    total_results = len(results)
    total_intent_errors = sum(
        intent_confusion_matrix[exp][pred]
        for exp in intent_confusion_matrix
        for pred in intent_confusion_matrix[exp]
        if exp != pred
    )
    
    # Most confused intent
    max_confusion = None
    max_confusion_count = 0
    for expected, preds in intent_confusion_matrix.items():
        for predicted, count in preds.items():
            if expected != predicted and count > max_confusion_count:
                max_confusion = (expected, predicted, count)
                max_confusion_count = count
    
    print("1. INTENT CLASSIFICATION")
    print(f"   - Overall intent error rate: {total_intent_errors}/{total_results} ({total_intent_errors/total_results*100:.1f}%)")
    print(f"   - Overall intent accuracy: {(total_results-total_intent_errors)/total_results*100:.1f}%")
    
    if max_confusion:
        exp, pred, cnt = max_confusion
        print(f"   - Most common confusion: '{exp}' -> '{pred}' ({cnt} times)")
    
    print()
    print("2. ENTITY EXTRACTION")
    total_entity_failures = sum(entity_failures.values())
    print(f"   - Total entity extraction issues: {total_entity_failures}")
    if not_extracted:
        print(f"   - Entities not extracted at all: {len(not_extracted)} types")
    if wrong_values:
        print(f"   - Entities with wrong values: {len(wrong_values)} types")
    
    print()
    print("3. LANGUAGE PERFORMANCE")
    language_stats = defaultdict(lambda: {"total": 0, "errors": 0})
    for result in results:
        lang = result["language"]
        language_stats[lang]["total"] += 1
        if result["expected_intent"] != result["predicted_intent"]:
            language_stats[lang]["errors"] += 1
    
    for lang in sorted(language_stats.keys()):
        stats = language_stats[lang]
        accuracy = (1 - stats["errors"]/stats["total"]) * 100
        print(f"   {lang:10}: {accuracy:5.1f}% accuracy ({stats['errors']}/{stats['total']} errors)")
    
    print()
    print("4. DIFFICULTY PERFORMANCE")
    diff_stats = defaultdict(lambda: {"total": 0, "errors": 0})
    for result in results:
        diff = result["difficulty"]
        diff_stats[diff]["total"] += 1
        if result["expected_intent"] != result["predicted_intent"]:
            diff_stats[diff]["errors"] += 1
    
    for diff in ["easy", "medium", "hard"]:
        stats = diff_stats[diff]
        if stats["total"] > 0:
            accuracy = (1 - stats["errors"]/stats["total"]) * 100
            print(f"   {diff:10}: {accuracy:5.1f}% accuracy ({stats['errors']}/{stats['total']} errors)")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS FOR IMPROVEMENT")
    print("=" * 80)
    print()
    print("PRIORITY 1 - ENTITY EXTRACTION (0% overall accuracy)")
    print("  - Investigate entity_extractor.py regex patterns")
    print("  - Check: budget_rupees, land_size_hectares, location, enterprise")
    print("  - Problem: 100% extraction rate but WRONG VALUES suggests regex mismatch")
    print()
    print("PRIORITY 2 - LIVELIHOOD INTENT DETECTION (28% accuracy)")
    print("  - This is the PRIMARY use case (32 of 60 examples)")
    print("  - Currently only 9/32 correct (28%)")
    print("  - Often confused with general_question intent")
    print()
    print("PRIORITY 3 - HINDI/ENGLISH LANGUAGES (29-41% accuracy)")
    print("  - Marathi: 54% accuracy (best)")
    print("  - Hindi: 41% accuracy")
    print("  - English: 41% accuracy")
    print("  - Suggests language-specific patterns need work")
    print()
    print("PRIORITY 4 - COMPLEX QUERIES (29-38% accuracy on medium/hard)")
    print("  - Easy queries: 77% accuracy")
    print("  - Hard queries: 29% accuracy (48 percentage point drop)")
    print("  - Suggests deterministic patterns fail with complexity")
    print()


if __name__ == "__main__":
    analyze_errors()
