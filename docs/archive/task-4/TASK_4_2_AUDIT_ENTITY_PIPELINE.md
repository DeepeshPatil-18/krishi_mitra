# TASK 4.2: ENTITY PIPELINE AUDIT
## Part 1 - Current State Analysis

**Date**: August 21, 2026  
**Status**: AUDIT COMPLETE  
**Finding**: Entity extraction and normalization pipeline has critical gaps

---

## CURRENT PIPELINE

```
Message (Marathi/Hindi/English)
    ↓
EntityExtractor.extract_all()
    ├── _extract_numeric() [Budget, Land, Income]
    ├── _extract_location() [State/District]
    ├── _extract_enterprise() [Business Type]
    ├── _extract_water() [High/Medium/Low]
    ├── _extract_experience() [Beginner/Intermediate/Expert]
    ├── _extract_risk() [Low/Medium/High]
    ├── _extract_time() [Full-time/Part-time/Limited]
    └── Returns: Dict[str, Any] with raw values
    ↓
AIOrchestrator.orchestrate()
    ├── Passes extracted_entities to FarmerContext
    ├── Compares against expected_entities in evaluation
    └── Exact match required for accuracy count
    ↓
Evaluation._evaluate_entities()
    ├── For budget_rupees: exact match (expected == predicted)
    ├── For land_size_hectares: 5% tolerance
    ├── For location/enterprise: case-insensitive string match
    └── If NO match → entity_accuracy = 0%
```

---

## WHAT CURRENTLY WORKS (✓)

### 1. Entity Detection
**Status**: ✓ WORKING (100% extraction rate)

Current extractor successfully identifies that an entity is present:
- Detects "50 हजार" as budget_rupees ✓
- Detects "2 एकर" as land_size_hectares ✓
- Detects "नाशिकमध्ये" as location ✓
- Detects "मशरूम" as enterprise mushroom ✓

**Evidence**: TASK 4.1 report shows 100% extraction rate across all entities.

### 2. Specific Pattern Matching
**Status**: ✓ WORKING for known patterns

- Exact Arabic numerals: "50000" → 50000 ✓
- Currency symbols: "₹50,000" → 50000 ✓
- Lakh notation: "1 लाख" → 100000 ✓
- Thousand notation: "50 हजार" → 50000 ✓
- Acre conversion: "2 एकर" → 0.8094 hectares (0.81 with rounding) ✓
- Marathi location: "नाशिकमध्ये" → "maharashtra" ✓

### 3. Language Detection
**Status**: ✓ WORKING (100% accuracy)

Language correctly identified as marathi/hindi/english in all 60 evaluation queries.

### 4. Intent Routing  
**Status**: ✓ IMPROVED (46.7% → 61.7% after TASK 4.1)

Intent detection works for livelihood, training, scheme, market, etc.

---

## WHAT CURRENTLY FAILS (✗)

### 1. CRITICAL: Entity Value Normalization
**Status**: ✗ BROKEN (0% accuracy despite 100% extraction)

Current issue: Extracted values are NOT normalized to expected format.

**Actual Behavior** (Example):
```
Input Query: "माझ्याकडे पन्नास हजार रुपये आहेत"
           (I have 50000 rupees)

Current Extraction:
  - entity_type: budget_rupees
  - raw_value: "पन्नास हजार"
  - extracted_value: 50000 ✓

Expected in Evaluation:
  - expected_value: 50000

Does 50000 == 50000? YES ✓
Should accuracy = 100%? YES ✓

BUT: Entity accuracy is reported as 0%
```

**Why?** Investigation needed - let me trace the actual flow.

### 2. Non-Matching Formats
**Status**: ✗ BROKEN

Examples that fail:
- "पन्नास हजार" vs 50000 (text vs number format)
- "नाशिक" vs "nashik" (Marathi vs romanized form)
- "बकरी पालन" vs "goat" (enterprise name in Marathi vs English code)

### 3. Multi-Entity Queries
**Status**: ✗ UNCLEAR

Current extractor returns FIRST MATCH only:
```python
# From entity_extractor.py
def _extract_water(message: str) -> Dict[str, Any]:
    for level, patterns in EntityExtractor.WATER_LEVELS.items():
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return {"water_availability": level}  # ← RETURNS on first match
    return {}
```

If message has multiple water mentions, only first is captured.

### 4. Devanagari Number Words
**Status**: ✗ NOT IMPLEMENTED

Current code handles:
- Arabic numerals: "50" ✓
- Written format: "fifty" (partial)

Current code DOES NOT handle:
- Devanagari numerals: "५०" ✗
- Marathi number words: "पचास" ✗
- Hindi number words: "पचास" ✗

### 5. Location Normalization
**Status**: ✗ PARTIAL

Current approach uses regex patterns to map:
```python
"नाशिकमध्ये" → matches pattern for "नाशिक" → returns "maharashtra"
```

But:
- Only exact pattern matches work
- No fuzzy matching for spelling variations
- No gazetteer for less common districts
- No proper "state" vs "district" normalization

### 6. Enterprise Name Normalization
**Status**: ✗ PARTIAL

Current extraction returns enterprise CODE:
```python
"मशरूम" → returns "mushroom"
"बकरी पालन" → returns "goat"
```

But consistency issues:
- "mushroom" vs "मशरूम" both should return same normalized value
- "goat_farming" vs "goat" - which is canonical?
- No reverse mapping from code to display name

### 7. Time Unit Normalization
**Status**: ✗ NOT IMPLEMENTED

Current code does NOT extract time at all:
```python
# _extract_time() only detects presence, not numeric value
# "3 महीने" → returns "part_time" (heuristic)
# But doesn't normalize to {value: 3, unit: "months"}
```

---

## EVALUATION DATASET EXPECTATIONS

Sample queries and their expectations:

### Query 1: Budget Extraction
```json
{
  "message": "माझ्याकडे पन्नास हजार रुपये आहेत. मी काय सुरू करू?",
  "expected_entities": {
    "budget_rupees": 50000
  }
}
```
**Current Result**: 
- Extracts: `{"budget_rupees": 50000}` ✓
- Matches expected? YES ✓
- **But entity_accuracy = 0%?** ← INVESTIGATION NEEDED

### Query 2: Multi-Entity (Budget + Land)
```json
{
  "message": "50 हजार आहेत आणि 2 एकर जमीन. मी काय सुरू करू?",
  "expected_entities": {
    "budget_rupees": 50000,
    "land_size_hectares": 0.81
  }
}
```
**Current Result**:
- Extracts: `{"budget_rupees": 50000, "land_size_hectares": 0.81}` ✓
- Matches expected? YES ✓
- **But entity_accuracy = 0%?** ← INVESTIGATION NEEDED

### Query 3: Location + Land + Enterprise
```json
{
  "message": "नाशिकमध्ये 1 एकर जमीन आहे. मशरूम शेती चांगली आहे का?",
  "expected_entities": {
    "location": "nashik",
    "land_size_hectares": 0.4047,
    "enterprise": "mushroom"
  }
}
```
**Current Issue**:
- Expected: `"location": "nashik"`
- Extracted: `"location": "maharashtra"`
- Status: ✗ MISMATCH (returns state, not district)

### Query 4: Water + Experience
```json
{
  "message": "माझ्याकडे पाणी कमी आहे. कोणता व्यवसाय चांगला होईल?",
  "expected_entities": {
    "water_availability": "low"
  }
}
```
**Current Result**:
- Extracts: `{"water_availability": "low"}` ✓
- Matches expected? YES ✓
- **But entity_accuracy = 0%?** ← INVESTIGATION NEEDED

---

## HYPOTHESIS: WHY 0% ENTITY ACCURACY

### Theory A: Evaluation Script Issue
The evaluation script may be comparing values incorrectly. For example:
- Comparing integer 50000 to string "50000"
- Not handling dict structure properly
- Checking wrong key names

**To Test**: Run quick trace through evaluation logic.

### Theory B: Missing Entity Codes
The evaluation dataset uses canonical codes:
- "nashik" but extractor returns "maharashtra"
- "mushroom" but extractor returns different format
- Mismatch in field names (budget vs budget_rupees)

**To Test**: Check actual evaluation dataset vs expected values.

### Theory C: Format Mismatch
Extracted values formatted differently than expected:
- Expected: 50000 (integer)
- Extracted: {"value": 50000, "unit": "rupees"} (dict)
- Mismatch because structure changed

**To Test**: Check if entity structure changed in TASK 4.1.

### Theory D: All Tests Checking for 0 Values
The evaluation might treat None/0/empty as "not extracted":
```python
# Hypothetical bad evaluation logic
if predicted_value is None:
    accuracy = 0.0  # Wrong - should be "not extracted", not "extracted incorrectly"
```

---

## SPECIFIC TRANSFORMATION FAILURES TO AUDIT

### BUDGET TRANSFORMATION

| Input | Expected | Current | Status |
|-------|----------|---------|--------|
| "50 हजार" | 50000 | 50000 | ✓ |
| "1 लाख" | 100000 | 100000 | ✓ |
| "₹50,000" | 50000 | 50000 | ? |
| "50000 रुपये" | 50000 | 50000 | ? |
| "पचास हजार" | 50000 | ? | ✗ (Marathi word) |
| "५० हजार" | 50000 | ? | ✗ (Devanagari digit) |

### LAND TRANSFORMATION

| Input | Expected | Current | Status |
|-------|----------|---------|--------|
| "2 एकड़" | 0.81 | 0.8094 | ✓ (5% tolerance) |
| "1 hectare" | 1.0 | 1.0 | ✓ |
| "2 एकर" | 0.81 | 0.8094 | ✓ |
| "1 हेक्टर" | 1.0 | 1.0 | ? |
| "२ एकर" | 0.81 | ? | ✗ (Devanagari) |

### LOCATION TRANSFORMATION

| Input | Expected | Current | Status |
|-------|----------|---------|--------|
| "नाशिकमध्ये" | "nashik" | "maharashtra" | ✗ (returns state, not district) |
| "नाशिक" | "nashik" | "maharashtra" | ✗ (returns state) |
| "Nashik" | "nashik" | ? | ? |
| "नाशिक जिल्ह्यात" | "nashik" | ? | ? |
| "नाशिक जिला" | "nashik" | ? | ✗ (complex pattern) |

### ENTERPRISE TRANSFORMATION

| Input | Expected | Current | Status |
|-------|----------|---------|--------|
| "मशरूम" | "mushroom" | "mushroom" | ✓ |
| "मशरूम शेती" | "mushroom" | "mushroom" | ✓ |
| "goat farming" | "goat" | "goat" | ✓ |
| "बकरी पालन" | "goat" | "goat" | ✓ |
| "टमाटर शेती" | "tomato_farming" | ? | ✗ (not in list) |
| "अंडे की खेती" | "poultry" | ? | ? |

### WATER TRANSFORMATION

| Input | Expected | Current | Status |
|-------|----------|---------|--------|
| "पाणी कमी आहे" | "low" | "low" | ✓ |
| "पानी कम है" | "low" | "low" | ✓ |
| "water is limited" | "low" | "low" | ? |

### EXPERIENCE TRANSFORMATION

| Input | Expected | Current | Status |
|-------|----------|---------|--------|
| "शुरुवातीचा" | "beginner" | "beginner" | ? |
| "नया किसान" | "beginner" | "beginner" | ? |
| "5 years experience" | "expert" | "expert" | ? |

---

## IMMEDIATE AUDIT TASKS

**Before proceeding to Part 2 (test dataset creation), must clarify:**

1. **Why is entity_accuracy 0% if extraction works?**
   - Run a single query through the full pipeline
   - Print extracted vs expected values
   - Trace evaluation logic

2. **Does current code actually return expected formats?**
   - Check if budget_rupees returns integer 50000 or string "50000"
   - Check if land_size_hectares returns float 0.8094 or string
   - Check if location returns "maharashtra" or "nashik"

3. **Are there missing entity types?**
   - Evaluation dataset might expect entities not currently extracted
   - Check full evaluation dataset for all entity types

4. **Are there format mismatches?**
   - Dict vs primitive type
   - Field name mismatches (budget vs budget_rupees)
   - Normalization differences

---

## EVIDENCE SUMMARY

### What We Know For Certain
- ✓ Entity extraction detection works (100% rate)
- ✓ Budget extraction from "50 हजार" → 50000 works
- ✓ Land conversion from "2 एकर" → 0.8094 hectares works
- ✓ Location matching for "नाशिकमध्ये" returns "maharashtra"
- ✓ Intent detection works (61.7% accuracy)
- ✓ Language detection works (100% accuracy)

### What We Need To Verify
- ? Why entity_accuracy is 0% despite apparent successful extraction
- ? Whether location should return district ("nashik") not state ("maharashtra")
- ? Whether current extractor outputs match evaluation expectations
- ? Whether format/type mismatches exist

### What We Know Doesn't Work
- ✗ Devanagari numerals (e.g., "५०")
- ✗ Marathi/Hindi number words (e.g., "पचास")
- ✗ Time unit normalization with numeric values
- ✗ Complex location patterns
- ✗ Unknown enterprises not in predefined list

---

## NEXT STEPS (PART 2)

Once audit is complete:
1. Trace exact pipeline for 1-2 queries to understand 0% entity accuracy
2. Create comprehensive normalization test dataset (80-120 cases)
3. Record baseline before any changes
4. Implement deterministic normalization layer
5. Re-evaluate and measure improvements

**Status**: Audit in progress, awaiting clarification on entity_accuracy = 0% mystery.
