#!/usr/bin/env python3
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET_IDS = {
    'eval_001','eval_005','eval_009','eval_012','eval_018','eval_026',
    'eval_027','eval_028','eval_029','eval_030','eval_038','eval_040',
    'eval_044','eval_045','eval_046','eval_047','eval_051','eval_053',
    'eval_054','eval_060'
}

with open('data/evaluation/task_4_5_full_results.json', encoding='utf-8') as f:
    data = json.load(f)

for r in data['results']:
    if r['id'] in TARGET_IDS:
        print(f"=== {r['id']} [{r['language']}] ===")
        print(f"MSG:      {r['message']}")
        print(f"EXP_ENT:  {r['expected_entities']}")
        print(f"PRED_ENT: {r['predicted_entities']}")
        entity_matches = r.get('entity_matches', {})
        for etype, m in entity_matches.items():
            status = "OK" if m['match'] else "FAIL"
            print(f"  [{status}] {etype}: expected={m['expected']} predicted={m['predicted']}")
        print()
