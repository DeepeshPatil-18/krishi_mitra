#!/usr/bin/env python3
"""Analyze entity failures from task_4_4_results.json for TASK 4.5 audit"""

import json
import sys
from collections import defaultdict

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    with open('data/evaluation/task_4_5_full_results.json', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']
    print(f"Total results: {len(results)}")
    print()

    # ── Collect every entity failure ──────────────────────────────────────────
    entity_failures = []
    entity_successes = []
    for r in results:
        for etype, match_info in r.get('entity_matches', {}).items():
            record = {
                'id': r['id'],
                'language': r['language'],
                'difficulty': r['difficulty'],
                'entity_type': etype,
                'expected': match_info.get('expected'),
                'predicted': match_info.get('predicted'),
                'message': r['message'],
                'intent_match': r['intent_match'],
                'predicted_entities': r.get('predicted_entities', {}),
            }
            if match_info.get('match', False):
                entity_successes.append(record)
            else:
                entity_failures.append(record)

    total_entity_cases = len(entity_failures) + len(entity_successes)
    print(f"Total entity cases evaluated: {total_entity_cases}")
    print(f"Entity successes:  {len(entity_successes)}")
    print(f"Entity failures:   {len(entity_failures)}")
    print()

    # ── Failures by type ──────────────────────────────────────────────────────
    by_type = defaultdict(list)
    for f in entity_failures:
        by_type[f['entity_type']].append(f)

    print("=" * 80)
    print("ENTITY FAILURES BY TYPE")
    print("=" * 80)
    for etype in sorted(by_type.keys()):
        cases = by_type[etype]
        print(f"\n{etype.upper()} — {len(cases)} failures")
        print("-" * 60)
        for c in cases:
            print(f"  [{c['id']}] {c['language']} / {c['difficulty']}")
            print(f"    MSG:       {c['message']}")
            print(f"    EXPECTED:  {c['expected']}")
            print(f"    PREDICTED: {c['predicted']}")
            print(f"    ALL_PRED:  {c['predicted_entities']}")
            print()

    # ── Successes by type (to understand what IS working) ────────────────────
    print("=" * 80)
    print("ENTITY SUCCESSES BY TYPE")
    print("=" * 80)
    succ_by_type = defaultdict(list)
    for s in entity_successes:
        succ_by_type[s['entity_type']].append(s)
    for etype in sorted(succ_by_type.keys()):
        cases = succ_by_type[etype]
        print(f"  {etype}: {len(cases)} successes")
        for c in cases[:3]:   # show at most 3
            print(f"    [{c['id']}] {c['message'][:70]}")
            print(f"           expected={c['expected']} predicted={c['predicted']}")
        if len(cases) > 3:
            print(f"    ... and {len(cases)-3} more")
        print()

    # ── ROI analysis ─────────────────────────────────────────────────────────
    print("=" * 80)
    print("ROI ANALYSIS — failures per entity type")
    print("=" * 80)
    for etype in sorted(by_type.keys()):
        cnt = len(by_type[etype])
        total_expected_for_type = cnt + len(succ_by_type.get(etype, []))
        print(f"  {etype}: {cnt} failures / {total_expected_for_type} total "
              f"({cnt/total_entity_cases*100:.1f}% of all entity cases)")

    # ── False positives: entities predicted but NOT expected ─────────────────
    print()
    print("=" * 80)
    print("FALSE POSITIVES — entities predicted but not expected")
    print("=" * 80)
    fp_count = 0
    for r in results:
        predicted = r.get('predicted_entities', {})
        expected_keys = set(r.get('expected_entities', {}).keys())
        for etype, val in predicted.items():
            if etype not in expected_keys:
                print(f"  [{r['id']}] {r['language']} — extra {etype}={val}")
                print(f"    MSG: {r['message']}")
                fp_count += 1
    print(f"  Total false positives: {fp_count}")

if __name__ == '__main__':
    main()
