# TASK 4.3: Failure-Driven Optimization + Semantic Gap Assessment
## Part 1-3 Complete: Baseline + Failure Analysis

**Date**: August 22, 2026  
**Status**: BASELINE CREATED, READY FOR FAILURE TAXONOMY  

---

## PART 1 & 2: AUDIT + BASELINE COMPLETE

### TASK 4.2 Results Confirmed (BASELINE)
- **Intent Accuracy**: 61.7%
- **Entity Accuracy**: 46.8% (0% → 46.8%, 9x improvement via deterministic)
- **Language Accuracy**: 71.7%
- **Test Pass Rate**: 92.3%

### Entity-Type Breakdown (BASELINE)
| Entity Type | Accuracy | Status |
|---|---|---|
| enterprise | 90.5% | ✓ Excellent |
| risk_tolerance | 100% | ✓ Perfect |
| water_availability | 66.7% | ✓ Good |
| budget_rupees | 52.9% | ⚠ Partial |
| experience_level | 33.3% | ✗ Poor |
| land_size_hectares | 12.5% | ✗ Critical |
| location | 0% | ✗ Broken |
| time_availability | 0% | ? Not in dataset |
| willingness_to_learn | 0% | ? Not in dataset |

---

## PART 3: FAILURE TAXONOMY (TO BE COMPLETED)

### Failure Categories Framework

```
1. PARSER_BUG
   Definition: Extractor fails to detect entity that IS present in message
   Example: "50 हजार" not extracted because Hindi word parsing incomplete
   
2. MISSING_PATTERN
   Definition: Normalizer lacks pattern for valid input format
   Example: "1.5 एकड़" (with decimal) not handled
   
3. UNIT_CONVERSION
   Definition: Measurement conversion incorrect or missing
   Example: Acre to hectare conversion factor wrong
   
4. LANGUAGE_VARIATION
   Definition: Hindi/Marathi spelling or grammar variant not handled
   Example: "एकर" vs "एकड़" both valid, only one recognized
   
5. AMBIGUOUS_CONTEXT
   Definition: Multiple valid interpretations; normalizer guesses wrong
   Example: "बजेट" could mean monthly or annual budget
   
6. SEMANTIC_INTERPRETATION
   Definition: Entity value correct but semantic meaning differs from expectation
   Example: "experienced farmer" → normalizer returns "expert", expects "intermediate"
   
7. MISSING_LOOKUP
   Definition: Dictionary/mapping entry missing
   Example: "नाशिक" → should map to nashik district, but entry missing
   
8. TOLERANCE_MISMATCH
   Definition: Value within tolerance but evaluation criteria too strict
   Example: 49,500 vs 50,000 (±1% close) but fails exact match
   
9. INCOMPLETE_DATA
   Definition: User query missing required information
   Example: Query mentions "farming" but no specific entity values provided
   
10. EDGE_CASE
    Definition: Rare but valid edge case not covered
    Example: Fractional hectares (0.25 ha) not tested
    
11. FALSE_POSITIVE
    Definition: Normalizer extracts something that isn't there
    Example: Text "no water" parsed as water_availability=high (negation ignored)
    
12. MALFORMED_OUTPUT
    Definition: Normalizer returns wrong type/format
    Example: Returns string "50" instead of integer 50
```

---

## CURRENT DETERMINISTIC NORMALIZER STATUS

### What Works Well
- **Enterprise Extraction** (90.5%): Marathi/Hindi keywords matched effectively
- **Risk Tolerance** (100%): Simple keyword matching catches all cases
- **Water Availability** (66.7%): Pattern recognition effective
- **Budget/Numbers** (52.9%): Arabic and Devanagari numerals handled, but ranges/approximations incomplete

### Critical Gaps (Lowest Accuracy)
- **Land Size** (12.5%): Unit conversion broken or inconsistent
- **Experience Level** (33.3%): Year-based detection unreliable
- **Location** (0%): Either missing from dataset or complete failure in mapping

### EntityNormalizer Methods Inventory
```python
normalize_number()                  # Marathi/Hindi word numbers, Devanagari digits
normalize_land_size()              # Acre/hectare conversion (needs fix)
normalize_location()               # District mapping (needs expansion)
normalize_time_numeric()           # Duration parsing (महीने, months)
normalize_water_availability()     # High/medium/low pattern matching
normalize_experience_level()       # Keyword + year-based detection
normalize_risk_tolerance()         # Keyword matching (perfect)
normalize_time_availability()      # Full-time/part-time detection
```

---

## NEXT STEPS (PARTS 4-13)

### Part 4: Prioritize by ROI
Create table with Frequency × Impact ÷ Complexity:
- Frequency: How many queries affected (from baseline failures)
- Impact: How much accuracy increase if fixed (~% points)
- Complexity: Difficulty to implement (1=trivial, 5=very complex)
- ROI = (Frequency × Impact) / Complexity

### Part 5: Implement Highest-ROI Deterministic Fixes
- Fix land_size_hectares conversion (likely high ROI)
- Expand location mapping for common districts
- Add missing patterns for budget ranges

### Part 6-7: Avoid Regex Explosion
- Track # of special cases added
- If > 15 special cases per entity, stop and note as "brittle"
- Prefer data-driven lookup tables over hardcoded rules

### Part 8: Semantic Gap Assessment
- Categorize remaining failures into deterministic vs semantic
- Semantic = requires understanding context/intent, not just pattern matching

### Part 9: Intent Detection Analysis
- Create confusion matrix for intents
- Identify which intents are hardest to recognize

### Part 10: Entity Extraction Analysis
- By language, by difficulty, by entity type
- Identify patterns in failures

### Part 11-12: Regression Testing
- Run evaluation after each fix
- Ensure improvement > 2% or 3 percentage points
- If improvement < 2%, stop that fix attempt

### Part 13-15: Decision Framework
**If improvements are strong (>3% per fix)**: Continue deterministic approach
**If improvements plateau or complexity grows**: Recommend hybrid ML or more data
**Stop Condition**: If any of:
- Improvement < ~3% per iteration
- Fixes require disproportionately many special cases
- False positives increase
- Remaining failures are predominantly semantic
- Deterministic logic becomes difficult to maintain

---

## CRITICAL RULE: NO REGEX EXPLOSION
- Track number of rules/patterns added
- If adding > 5 patterns per entity type per fix iteration, re-evaluate
- Prefer lookup tables (extensible) over hardcoded regex (brittle)

---

## Baseline File Saved
**Location**: `data/evaluation/task_4_3_baseline.json`

Contains:
- Overall metrics (intent, entity, language, capability accuracy)
- By-entity-type breakdown with accuracy
- Task 4 comparison showing +9x improvement
- Deterministic normalizer status
- Key findings summary

File ready for comparison after deterministic fixes are implemented.
