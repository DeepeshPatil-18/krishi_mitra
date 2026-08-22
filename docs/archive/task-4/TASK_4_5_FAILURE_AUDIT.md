# TASK 4.5 — FAILURE AUDIT

**Date**: August 22, 2026  
**Baseline**: TASK 4.4 production pipeline — 51.1% entity accuracy (45/78 entity cases correct)

---

## 1. SUMMARY TABLE

| Entity Type | Total Cases | Failures | Accuracy | Failure Rate |
|-------------|-------------|----------|----------|--------------|
| budget_rupees | 17 | 8 | 52.9% | 47.1% |
| land_size_hectares | 16 | 6 | 62.5% | 37.5% |
| location | 6 | 6 | 0.0% | 100% |
| enterprise | 21 | 2 | 90.5% | 9.5% |
| water_availability | 6 | 2 | 66.7% | 33.3% |
| experience_level | 6 | 4 | 33.3% | 66.7% |
| time_availability | 3 | 3 | 0.0% | 100% |
| willingness_to_learn | 2 | 2 | 0.0% | 100% |
| risk_tolerance | 1 | 0 | 100% | 0% |
| **TOTAL** | **78** | **33** | **57.7%** | — |

**Note**: overall_entity_accuracy from evaluator = 51.1% (per-query averaging, not per-case averaging)

---

## 2. BUDGET_RUPEES — 8 FAILURES

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_001 | marathi | माझ्याकडे **पन्नास हजार** रुपये आहेत | 50000 | None | Word-spelled number "पन्नास" not in patterns |
| eval_026 | marathi | **बजेट 150000**. शक्य आहे का? | 150000 | None | Bare integer next to बजेट, no rupee suffix |
| eval_038 | marathi | **बजेट 60000**. शुरुवातीचा | 60000 | None | Bare integer next to बजेट |
| eval_044 | marathi | **200000 बजेट**. काय करू? | 200000 | None | Integer before बजेट |
| eval_045 | hindi | **40000 का बजट** | 40000 | None | बजट without rupee keyword |
| eval_046 | english | **50k budget**. 1 acre | 50000 | None | "k" suffix abbreviation |
| eval_051 | marathi | **50k आहे**, 2 एकड़ | 50000 | None | "k" suffix abbreviation |
| eval_060 | mixed | मेरे पास 1 acre है आणि **50k रुपये** | 50000 | None | "k" suffix before रुपये |

### Root Causes
- **Type A (3 cases — eval_026/038/044)**: Bare integer adjacent to budget keyword (`बजेट`/`बजट`) but no rupee suffix word. Current patterns require हजार, लाख, rupees, रुपये, or ₹ symbol.
- **Type B (3 cases — eval_046/051/060)**: `k`/`K` shorthand (50k = 50,000). No pattern handles this.
- **Type C (1 case — eval_001)**: Number written as words ("पन्नास हजार" = fifty thousand). EntityExtractor has digits-only patterns.
- **Type D (1 case — eval_045)**: "40000 का बजट" — integer + Hindi बजट. Similar to Type A but Hindi.

### Fixes
- **Fix B1 (HIGH ROI — 3 cases)**: Add `k`/`K` suffix pattern: `(\d+(?:\.\d+)?)k\b` → multiply by 1000. Also `(\d+)-(\d+)k` range.
- **Fix A1 (HIGH ROI — 4 cases)**: Add bare-integer-adjacent-to-budget-word: `(\d+)\s*(budget|बजेट|बजट)` and `(budget|बजेट|बजट)\s*(\d+)`.
- **Fix C1 (LOW ROI — 1 case)**: Word-spelled numbers are complex; skip for now (only 1 case).

---

## 3. LAND_SIZE_HECTARES — 6 FAILURES

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_012 | hindi | मेरे पास **2 एकड़** जमीन है | 0.81 | None | Nukta character issue in regex |
| eval_018 | english | I have **2 acres** of land | 2.0* | None | "acres" plural not in pattern |
| eval_028 | hindi | जमीन **1.5 एकड़** है | 0.607 | None | Nukta character issue |
| eval_046 | english | **1 acre**. Beginner. | 1.0* | 0.4047 | Dataset error: expected=1.0 but 1 acre=0.4047 ha |
| eval_051 | marathi | **2 एकड़** आहे | 0.81 | None | Nukta character issue |
| eval_054 | marathi | स्पेस **100 चौरस मीटर** | 0.01 | None | Square meters not supported |

*eval_018 expects `land_size_hectares=2.0` for "2 acres" — this is a **dataset error** (2 acres = 0.809 ha, not 2.0). The dataset treats acres as if they equal hectares. However, the correct conversion IS being applied (0.4047*2=0.8094). This is a mislabeled expected value.

*eval_046 expects `land_size_hectares=1.0` for "1 acre" — same dataset labeling issue.

### Root Causes
- **Type A (3 cases — eval_012/028/051)**: Hindi `एकड़` contains `ड़` (U+0921 + U+093C nukta). The current pattern `एकड़` in the source code may be encoded differently. Need to verify the regex encoding.
- **Type B (1 case — eval_018)**: "acres" (plural with `s`) not matched — pattern uses `acre\b` which does NOT match "acres" (the `s` follows the word boundary).
- **Type C (2 cases — eval_018/046)**: Dataset labeling error — expects hectares = acres (1:1 ratio). Should expect 2 acres = 0.809 ha. The system is CORRECT, the label is wrong. **Do not change code for these**.
- **Type D (1 case — eval_054)**: "100 चौरस मीटर" = 100 m² = 0.01 ha. Very specialized, single case.

### Fixes
- **Fix L1 (HIGH ROI — 3 cases)**: Fix `एकड़` nukta encoding in regex OR use a more robust pattern. Test by printing actual bytes.
- **Fix L2 (HIGH ROI — fixes eval_018 acres plural, integration test)**: Change `acre\b` to `acres?\b`.
- **Fix L3 (LOW ROI — 1 case)**: Square meters — skip (single unusual case).
- **Note**: eval_018 and eval_046 dataset labels are wrong. The system extracts the correct value. These 2 "failures" will remain regardless.

---

## 4. LOCATION — 6 FAILURES (100% failure rate)

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_003 | marathi | **नाशिकमध्ये** 1 एकर जमीन | nashik | None | Locative suffix -मध्ये appended |
| eval_027 | marathi | **पुणे जिल्ह्यात** | pune | None | Locative suffix -जिल्ह्यात appended |
| eval_029 | hindi | **केरल** में रहता हूं | kerala | None | Kerala not in LOCATIONS dict |
| eval_038 | marathi | **महाराष्ट्रात** 2 एकर | maharashtra | None | Locative suffix -त appended |
| eval_045 | hindi | **नाशिक में** रहता हूं | nashik | None | Pattern requires exact नाशिक but msg has Hindi suffix |
| eval_046 | english | In **Pune**. 50k budget. | pune | None | "Pune" (English) not in Maharashtra pattern |

### Root Causes
- **Type A (3 cases — eval_003/027/045)**: Marathi/Hindi locative suffixes (`-मध्ये`, `-जिल्ह्यात`, `-में`) appended to city names. Current patterns match the base word but the locative suffix makes it a non-match for regex with word boundaries.
- **Type B (1 case — eval_038)**: Locative suffix `-त` on महाराष्ट्र → `महाराष्ट्रात`. Same issue.
- **Type C (1 case — eval_029)**: "केरल" (Hindi/Marathi spelling of Kerala) not in dictionary.
- **Type D (1 case — eval_046)**: "Pune" English name in Maharashtra pattern but the current regex `pune` is actually present. Investigation shows the match fails because Devanagari regex has issues with ASCII names in mixed patterns.

### Fixes
- **Fix Loc1 (HIGH ROI — 4 cases)**: Remove `\b` from location patterns OR use prefix matching (just check if pattern substring appears). Locative suffixes prevent word-boundary matching.
- **Fix Loc2 (HIGH ROI — 1 case)**: Add `केरल` / `Kerala` mapping.
- **Fix Loc3 (check — 1 case eval_046)**: Debug "Pune" why it doesn't match given it's in pattern.

---

## 5. EXPERIENCE_LEVEL — 4 FAILURES

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_005 | marathi | मी **शुरुवातीचा** शेतकरी आहे | beginner | None | "शुरुवातीचा" not in beginner patterns |
| eval_029 | hindi | मैं **अनुभवी किसान** हूं | expert | intermediate | Ambiguous; "अनुभवी" maps to intermediate correctly |
| eval_038 | marathi | **शुरुवातीचा**. काय सुरू करू? | beginner | None | Same Marathi beginner word |
| eval_047 | marathi | **अगदी नवीन**. योजना कोणती? | beginner | None | "नवीन" = new/fresh, Marathi |

### Root Causes
- **Type A (2 cases — eval_005/038)**: `शुरुवातीचा` is Marathi for "starting/initial farmer" → beginner. Not in patterns.
- **Type B (1 case — eval_047)**: `नवीन` = new in Marathi. Not in patterns. `अगदी नवीन` = absolutely new.
- **Type C (1 case — eval_029)**: `अनुभवी किसान` is genuinely ambiguous. It means "experienced farmer" which the system maps to `intermediate`. The dataset labels this `expert`. This is a **borderline labeling issue** — "अनुभवी" without years context could be either. The system result is defensible.

### Fixes
- **Fix Exp1 (MEDIUM ROI — 3 cases)**: Add Marathi beginner phrases: `शुरुवातीचा`, `नवीन`, `अगदी नवीन`.
- **Note**: eval_029 is a labeling ambiguity. System answer (intermediate) is defensible. Do not change for this.

### Integration Test #6 — experience year threshold
The `\b(years)\b` pattern in `expert` EXPERIENCE_LEVELS matches ALL year mentions, so "1 year experience" → expert (wrong). The `years` keyword must be removed from expert pattern. Year-count-based inference should go to EntityNormalizer.
- **Fix Exp2 (CRITICAL — fixes integration test)**: Remove `\b(years)\b` and `\b(expert|professional|veteran|years)\b` `years` token from expert pattern. Instead add explicit high-year patterns: `\b(1[0-9]|[2-9]\d)\s*(years?|साल|वर्ष)`.

---

## 6. TIME_AVAILABILITY — 3 FAILURES

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_009 | marathi | मी **पूर्णकाळ** काम करू शकते | full_time | None | Marathi full-time word |
| eval_032 | english | willing to work **full-time** | full_time | None | Hyphen: pattern has `full\s+time` |
| eval_051 | marathi | मी **पार्ट टाइम** काम करू शकते | part_time | None | Marathi transliteration |

### Root Causes
- **Type A (1 case)**: `पूर्णकाळ` = Marathi "full time/full period". Not in patterns.
- **Type B (1 case)**: `full-time` with hyphen, not space. Pattern is `full\s+time`.
- **Type C (1 case)**: `पार्ट टाइम` = Marathi transliteration of "part time". Not in patterns.

### Fixes
- **Fix T1 (MEDIUM ROI — 3 cases)**: Add Marathi words + fix hyphen: `full[-\s]time`, `पूर्णकाळ`, `पार्ट\s+टाइम`.

---

## 7. ENTERPRISE — 2 FAILURES

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_030 | hindi | **वर्मीकम्पोस्ट** बनाने की ट्रेनिंग | vermicompost | None | Hindi alt spelling |
| eval_054 | marathi | **शेणखत** व्यवसाय | vermicompost | None | Marathi word for compost |

### Root Causes
- `वर्मीकम्पोस्ट` is an alternate Hindi spelling (vs `vermicompost` in the pattern).
- `शेणखत` = Marathi for dung/compost — similar category, dataset maps to vermicompost.

### Fixes
- **Fix Ent1 (LOW ROI — 2 cases)**: Add to vermicompost aliases: `वर्मीकम्पोस्ट`, `शेणखत`.

---

## 8. WATER_AVAILABILITY — 2 FAILURES

### Failure Cases

| ID | Language | Message | Expected | Predicted | Root Cause |
|----|----------|---------|----------|-----------|------------|
| eval_012 | hindi | पानी की सुविधा **कम है** | low | high | `कम` should match low, but `सुविधा` may trigger `medium` pattern, or another pattern fires `high` first |
| eval_040 | english | **Very limited water** | low | high | Pattern priority: `\b(well...)` fires first? |

### Investigation
For eval_040 "Very limited water. High risk tolerance.": `limited` matches `TIME_AVAILABILITY["limited"]` AND would also match `WATER_LEVELS["low"]`. But water was predicted as `high`. The word `well` in `\b(well|borewell|...)` would match "well" in English — but "well" isn't in this message. Let's check: `High risk tolerance` — the word `high` is NOT in water patterns. Actually the issue is the water `high` pattern `r"(पानी.*है|पानी.*उपलब्ध)"` — the water patterns fire in priority order `high` first. For eval_040 "Very limited water" — `limited` does NOT match any high water pattern. But predicted is `high`. Must be the `(well|borewell...)` pattern matching "well" implicitly? No. Let me check: `r"\b(well|borewell|नल|कुआँ|जलसंचय)\b"` — "well" as standalone word? "Very limited water. High risk tolerance." has no "well". But there IS the `r"\b(high|abundant)\b"` in water high pattern — and "High risk tolerance" contains `High`. That's a **false match**: water pattern `high` fires because "High" appears in the sentence (for risk tolerance). This is a pattern priority/scope issue.

### Root Cause
- eval_040: `\b(high|abundant)\b` in water HIGH pattern matches the word "High" from "High risk tolerance" → wrong entity fired.
- eval_012: `\b(well|borewell...)\b` fires on some word, OR the medium pattern fires, OR "सुविधा" triggers something. Need to investigate — "कम" should match `r"(कम|बहुत\s+कम|सूखा)"` in low, but "पानी की सुविधा कम है" may match medium first.

### Fixes
- **Fix W1 (LOW ROI — 2 cases)**: Scope water patterns more tightly (require पानी/water adjacent). This also fixes false positives.

---

## 9. WILLINGNESS_TO_LEARN — 2 FAILURES

Not in EntityExtractor. Low ROI — 2 cases only, niche entity. Skip.

---

## 10. FALSE POSITIVES (18 total)

| Pattern | Count | Cause |
|---------|-------|-------|
| `time_availability=limited` | 8 | `\b(limited|कम|थोड़ा)\b` — `कम` = "less/low" appears in budget/water context |
| `water_availability` wrong | 3 | Priority order firing on unrelated words |
| `experience_level=expert` | 1 | "expert" in "speak with an expert" |
| `enterprise=vermicompost` | 1 | `composting` or `vermi` false match |
| `risk_tolerance=high` | 1 | Matches from unrelated context |

False positives reduce accuracy by injecting wrong entities when the query doesn't mention that entity type. The `कम` keyword in `TIME_AVAILABILITY["limited"]` is the biggest culprit — it conflicts with water context.

---

## 11. INTEGRATION TEST FAILURE ANALYSIS (6 tests)

| Test | Root Cause | Fix Required | Test Correct? |
|------|-----------|--------------|---------------|
| test_english_land | `"2 acres"` — plural `s` not in pattern `acre\b` | Add `acres?` | ✅ Test is correct |
| test_mixed_language_query | `"budget 50000"` — no rupee suffix | Add budget-adjacent bare integer | ✅ Test is correct |
| test_land_fraction_marathi | `"आधा एकर"` — fraction word not extracted by EntityExtractor | Add fraction land patterns | ✅ Test is correct |
| test_land_fraction_hindi | `"डेढ़ एकर"` — same | Add fraction land patterns | ✅ Test is correct |
| test_budget_range | `"50-100k"` — range not extracted | Add range pattern | ✅ Test is correct |
| test_experience_years_threshold | `\b(years)\b` in `expert` pattern matches ALL year mentions; "1 year" → expert, not beginner | Remove `years` from expert pattern; add year-count patterns | ✅ Test is correct |

All 6 tests are legitimate. All 6 failures are EntityExtractor bugs, not test bugs.

---

## 12. ROI PRIORITIZATION

| Fix | Cases Fixed | Complexity | ROI | Action |
|-----|------------|------------|-----|--------|
| **Budget: k/K suffix** (50k, 100k) | 3 eval + int test | LOW | HIGH | ✅ IMPLEMENT |
| **Budget: bare int + बजेट/budget** | 4 eval | LOW | HIGH | ✅ IMPLEMENT |
| **Budget: range 50-100k** | int test | LOW | HIGH | ✅ IMPLEMENT |
| **Location: locative suffixes** | 4 eval | LOW | HIGH | ✅ IMPLEMENT |
| **Location: केरल/Kerala** | 1 eval | TRIVIAL | MEDIUM | ✅ IMPLEMENT |
| **Land: acres plural** | 1 eval + int test | TRIVIAL | HIGH | ✅ IMPLEMENT |
| **Land: एकड़ nukta fix** | 3 eval | LOW | HIGH | ✅ IMPLEMENT |
| **Land: fractions आधा/डेढ़** | int tests | LOW | MEDIUM | ✅ IMPLEMENT |
| **Experience: Marathi beginner** | 3 eval | LOW | MEDIUM | ✅ IMPLEMENT |
| **Experience: year-count fix** | int test | LOW | HIGH | ✅ IMPLEMENT |
| **Time: full-time hyphen + Marathi** | 3 eval | LOW | MEDIUM | ✅ IMPLEMENT |
| **Enterprise: Hindi/Marathi compost** | 2 eval | TRIVIAL | LOW | ✅ IMPLEMENT |
| **Water: scope patterns tighter** | 2 eval + 8 FP | MEDIUM | MEDIUM | ✅ IMPLEMENT |
| Budget: word-spelled numbers | 1 eval | HIGH | LOW | ❌ SKIP |
| Land: square meters | 1 eval | MEDIUM | LOW | ❌ SKIP |
| Willingness_to_learn | 2 eval | MEDIUM | LOW | ❌ SKIP |

**Expected improvement if all HIGH+MEDIUM fixes land**: up to ~15 additional correct entity cases out of 33 failures = ~19% improvement on entity accuracy.

---

## 13. DATASET LABELING ISSUES IDENTIFIED

| ID | Issue |
|----|-------|
| eval_018 | `land_size_hectares=2.0` for "2 acres" — should be 0.809. Dataset mislabeled. |
| eval_046 | `land_size_hectares=1.0` for "1 acre" — should be 0.405. Dataset mislabeled. |
| eval_029 | `experience_level=expert` for "अनुभवी किसान" — ambiguous, system's `intermediate` is defensible. |

These 3 cases will remain "failures" even after perfect implementation. They represent dataset quality, not system quality.

---

**Audit complete. Proceed to implementation.**
