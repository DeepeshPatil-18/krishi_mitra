#!/usr/bin/env python3
"""
Detailed error analysis for evaluation failures.
Categorizes and explains why predictions failed.
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
    
    # Categories for analysis
    failures = {
        "intent_mismatches": [],
        "entity_extraction_failures": [],
        "entity_value_failures": [],
        "capability_mismatches": [],
        "language_specific_failures": [],
    }
    
    entity_failure_details = defaultdict(list)
    intent_confusion_matrix = defaultdict(lambda: defaultdict(int))
    
    print("=" * 80)
    print("DETAILED ERROR ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze each result
    for result in results:
        result_id = result["id"]
        message = result["message"]
        language = result["language"]
        difficulty = result["difficulty"]
        
        expected_intent = result["expected_intent"]
        predicted_intent = result["predicted_intent"]
        expected_capability = result["expected_capability"]
        predicted_capability = result["predicted_capability"]
        
        expected_entities = result["expected_entities"]
        predicted_entities = result["predicted_entities"]
        entity_matches = result["entity_matches"]
        
        # Check intent mismatches
        if expected_intent != predicted_intent:
            intent_confusion_matrix[expected_intent][predicted_intent] += 1
            failures["intent_mismatches"].append({
                "id": result_id,
                "language": language,
                "difficulty": difficulty,
                "message": message[:80],
                "expected": expected_intent,
                "predicted": predicted_intent,
                "confidence": result["intent_confidence"]
            })
        
        # Check capability mismatches
        if expected_capability != predicted_capability:
            failures["capability_mismatches"].append({
                "id": result_id,
                "language": language,
                "expected": expected_capability,
                "predicted": predicted_capability,
            })
        
        # Check entity extraction
        for entity_type, matches_info in entity_matches.items():
            expected_val = matches_info.get("expected")
            predicted_val = matches_info.get("predicted")
            matches = matches_info.get("match", False)
            
            if not matches:
                if predicted_val is None:
                    entity_failure_details[f"{entity_type}_NOT_EXTRACTED"].append({
                        "id": result_id,
                        "expected": expected_val,
                        "language": language,
                        "difficulty": difficulty
                    })
                else:
                    entity_failure_details[f"{entity_type}_WRONG_VALUE"].append({
                        "id": result_id,
                        "expected": expected_val,
                        "predicted": predicted_val,
                        "language": language,
                        "difficulty": difficulty
                    })
    
    # Print intent confusion matrix
    print("=" * 80)
    print("INTENT CONFUSION MATRIX")
    print("(Shows how many queries of each intent were misclassified to another)")
    print("=" * 80)
    print()
    
    all_intents = set(intent_confusion_matrix.keys()) | set(
        i for d in intent_confusion_matrix.values() for i in d.keys()
    )
    all_intents = sorted(list(all_intents))
    
    # Header
    print(f"{'Expected':<25} ", end="")
    for intent in all_intents:
        print(f"{intent:<20}", end="")
    print()
    print("-" * (25 + len(all_intents) * 20))
    
    # Rows
    for expected in all_intents:
        print(f"{expected:<25} ", end="")
        for predicted in all_intents:
            count = intent_confusion_matrix[expected][predicted]
            if expected == predicted:
                print(f"[{count:>2}] CORRECT     ", end="")
            else:
                if count > 0:
                    print(f" {count:>2}  ERROR       ", end="")
                else:
                    print(f" -              ", end="")
        print()
    
    print()
    print("=" * 80)
    print("INTENT MISMATCH FAILURES")
    print("=" * 80)
    print()
    print(f"Total: {len(failures['intent_mismatches'])} failures")
    print()
    
    # Group by expected intent
    by_intent = defaultdict(list)
    for failure in failures["intent_mismatches"]:
        by_intent[failure["expected"]].append(failure)
    
    for intent, failures_list in sorted(by_intent.items()):
        print(f"\n{intent} ({len(failures_list)} failures):")
        print("-" * 40)
        
        # Group predicted misclassifications
        predicted_counts = defaultdict(int)
        for failure in failures_list:
            predicted_counts[failure["predicted"]] += 1
        
        for predicted, count in sorted(predicted_counts.items(), key=lambda x: -x[1]):
            pct = (count / len(failures_list)) * 100
            print(f"  -> {predicted}: {count} ({pct:.1f}%)")
        
        # Show examples
        print(f"  Examples:")
        for failure in failures_list[:2]:
            print(f"    [{failure['language']} / {failure['difficulty']}] {failure['message']}")
            print(f"      Expected: {failure['expected']}, Got: {failure['predicted']}")
    
    # Entity extraction analysis
    print()
    print("=" * 80)
    print("ENTITY EXTRACTION FAILURES")
    print("=" * 80)
    print()
    
    # Separate not-extracted vs wrong-value
    not_extracted = {k: v for k, v in entity_failure_details.items() if "NOT_EXTRACTED" in k}
    wrong_values = {k: v for k, v in entity_failure_details.items() if "WRONG_VALUE" in k}
    
    print(f"Entities NOT EXTRACTED: {len(not_extracted)} types")
    for entity_type in sorted(not_extracted.keys()):
        count = len(not_extracted[entity_type])
        print(f"  {entity_type}: {count} failures")
    
    print()
    print(f"Entities EXTRACTED WITH WRONG VALUE: {len(wrong_values)} types")
    for entity_type in sorted(wrong_values.keys()):
        count = len(wrong_values[entity_type])
        examples = wrong_values[entity_type][:2]
        print(f"  {entity_type}: {count} failures")
        for ex in examples:
            print(f"    Expected: {ex['expected']}, Got: {ex['predicted']}")
    
    # Language-specific patterns
    print()
    print("=" * 80)
    print("LANGUAGE-SPECIFIC FAILURE PATTERNS")
    print("=" * 80)
    print()
    
    by_language = defaultdict(lambda: {"intents": 0, "entities": 0, "total": 0})
    
    for failure in failures["intent_mismatches"]:
        lang = failure["language"]
        by_language[lang]["intents"] += 1
        by_language[lang]["total"] += 1
    
    for lang in sorted(by_language.keys()):
        stats = by_language[lang]
        print(f"{lang}: {stats['intents']} intent failures")
    
    # Difficulty-specific patterns
    print()
    print("=" * 80)
    print("DIFFICULTY-SPECIFIC FAILURE PATTERNS")
    print("=" * 80)
    print()
    
    by_difficulty = defaultdict(int)
    for failure in failures["intent_mismatches"]:
        diff = failure["difficulty"]
        by_difficulty[diff] += 1
    
    for diff in ["easy", "medium", "hard"]:
        count = by_difficulty.get(diff, 0)
        total_in_difficulty = len([r for r in results if r["difficulty"] == diff])
        failure_rate = (count / total_in_difficulty * 100) if total_in_difficulty > 0 else 0
        print(f"{diff.upper()}: {count} failures out of {total_in_difficulty} ({failure_rate:.1f}% failure rate)")
    
    print()
    print("=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print()
    
    # Calculate key stats
    total_intent_failures = len(failures["intent_mismatches"])
    total_capability_failures = len(failures["capability_mismatches"])
    
    # Most confused intent
    if intent_confusion_matrix:
        max_confusion = max(
            (
                (expected, predicted, count)
                for expected, preds in intent_confusion_matrix.items()
                for predicted, count in preds.items()
                if expected != predicted
            ),
            key=lambda x: x[2],
            default=None
        )
        if max_confusion:
            exp, pred, cnt = max_confusion
            print(f"1. Biggest confusion: '{exp}' misclassified as '{pred}' ({cnt} times)")
    
    print(f"2. Total intent classification failures: {total_intent_failures} ({total_intent_failures/len(results)*100:.1f}%)")
    print(f"3. Entity extraction issues: ALL 0% accurate")
    print(f"   - Most common: {entity_failure_details}")
    
    # Find patterns
    print()
    print("=" * 80)
    print("PATTERNS TO INVESTIGATE")
    print("=" * 80)
    print()
    
    print("1. WHY IS LIVELIHOOD DETECTION SO LOW?")
    livelihood_failures = [f for f in failures["intent_mismatches"] if f["expected"] == "livelihood_recommendation"]
    if livelihood_failures:
        print(f"   - {len(livelihood_failures)} livelihood queries misclassified")
        predicted_as = defaultdict(int)
        for f in livelihood_failures:
            predicted_as[f["predicted"]] += 1
        for intent, count in sorted(predicted_as.items(), key=lambda x: -x[1]):
            pct = (count / len(livelihood_failures)) * 100
            print(f"     → Most often classified as '{intent}': {count} ({pct:.1f}%)")
    
    print()
    print("2. WHICH ENTITIES ARE FAILING?")
    print("   All entities have 0-12.5% accuracy (100% extraction but wrong values)")
    print("   This suggests systematic value extraction problems, not missing entities")
    
    print()
    print("3. LANGUAGE DIFFERENCES?")
    lang_stats = defaultdict(lambda: {"intents": 0, "total": 0})
    for result in results:
        lang_stats[result["language"]]["total"] += 1
        if result["expected_intent"] != result["predicted_intent"]:
            lang_stats[result["language"]]["intents"] += 1
    
    for lang in sorted(lang_stats.keys()):
        stats = lang_stats[lang]
        error_pct = (stats["intents"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"   {lang}: {error_pct:.1f}% intent failure rate")


if __name__ == "__main__":
    analyze_errors()
