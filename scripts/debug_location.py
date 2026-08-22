#!/usr/bin/env python3
"""Diagnose why location patterns pass unit tests but fail in production."""
import sys, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, 'd:\\krishimitra_backend')
from app.services.entity_extractor import EntityExtractor

# The 6 failing messages from the evaluation results
test_cases = [
    ("eval_003", "नाशिकमध्ये 1 एकर जमीन आहे. मशरूम शेती चांगली आहे का?", "nashik"),
    ("eval_027", "पुणे जिल्ह्यात कांद्याचा व्यवसाय करायचे आहे. योजना आहे का?", "pune"),
    ("eval_029", "मैं अनुभवी किसान हूं। केरल में रहता हूं। क्या करूं?", "kerala"),
    ("eval_038", "माझ्याकडे महाराष्ट्रात 2 एकर आहेत. बजेट 60000. शुरुवातीचा. काय सुरू करू?", "maharashtra"),
    ("eval_045", "नाशिक में रहता हूं। 40000 का बजट। कैसे शुरू करूं?", "nashik"),
    ("eval_046", "In Pune. 50k budget. 1 acre. Beginner. Help?", "pune"),
]

print("=== DIRECT EntityExtractor test ===\n")
for eid, msg, expected in test_cases:
    result = EntityExtractor.extract_all(msg)
    loc = result.get("location")
    status = "OK" if loc == expected else "FAIL"
    print(f"[{status}] {eid}")
    print(f"  msg:      {msg}")
    print(f"  expected: {expected}  got: {loc}")
    print()

# Now test same messages loaded FROM the JSON file (as they'd be in the pipeline)
print("=== Messages loaded from JSON file ===\n")
with open('data/evaluation/task_4_5_full_results.json', encoding='utf-8') as f:
    data = json.load(f)

target_ids = {c[0] for c in test_cases}
for r in data['results']:
    if r['id'] not in target_ids:
        continue
    msg = r['message']
    expected = r['expected_entities'].get('location')
    result = EntityExtractor.extract_all(msg)
    loc = result.get("location")
    status = "OK" if loc == expected else "FAIL"
    print(f"[{status}] {r['id']}")
    print(f"  msg:      {msg}")
    print(f"  expected: {expected}  got: {loc}")

    # Debug: test each pattern individually
    print("  Pattern checks:")
    for location, patterns in EntityExtractor.LOCATIONS.items():
        for pat in patterns:
            m = re.search(pat, msg, re.IGNORECASE)
            if m:
                print(f"    MATCH: location={location} pattern={pat!r} match={m.group()!r}")
    print()
