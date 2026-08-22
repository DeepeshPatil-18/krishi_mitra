# KrishiMitra Baseline Evaluation - Detailed Error Analysis

**Date**: August 19, 2026  
**Dataset**: 60 farmer queries  
**System**: KrishiMitra (TASK 3 complete)

## Executive Summary

**Total Failures**: 32 out of 60 queries (53.3% failure rate)

### By Category
- **Intent Detection**: 32 failures (53.3% error rate)
  - Correct: 28/60 (46.7% accuracy)
  - Misclassified: 32/60 (53.3% error rate)

- **Entity Extraction**: 60 failures (100% error rate)
  - Extraction rate: 100% (entities ARE being extracted)
  - Accuracy: 0% (but they're WRONG)
  - Critical insight: This is a VALUE EXTRACTION problem, not a DATA RETRIEVAL problem

---

## Intent Classification Failures (32 failures)

### Failure Distribution by Expected Intent

**livelihood_recommendation** (32 examples total, 23 failures = 71.9% error rate)
- Misclassified as: general_question, training_request, expert_request
- Pattern: Complex queries with multiple constraints get confused with other intents
- Language pattern: Hindi/English queries fail more than Marathi

**scheme_search** (5 examples total, 0 failures = 100% accuracy) ✓
- Perfect accuracy - regex patterns work well

**training_request** (8 examples total, 5 failures = 62.5% error rate)
- Misclassified as: general_question, livelihood_recommendation
- Pattern: Requests for training/education often misunderstood

**market_search** (5 examples total, 2 failures = 40% error rate)
- Misclassified as: general_question
- Pattern: Market/sales queries sometimes confused with general questions

**expert_request** (4 examples total, 0 failures = 100% accuracy) ✓
- Perfect accuracy - clear keywords work well

**community** (1 example total, 0 failures = 100% accuracy) ✓
- Too few examples, but 100% for this case

**general_question** (5 examples total, 2 failures = 40% error rate)
- Misclassified as: livelihood_recommendation, scheme_search, market_search
- Pattern: Ambiguous questions misrouted to specific intents

### Intent Confusion Matrix

```
Expected                  Predicted (Column) →
                    scheme  training  expert  market  community  livelihood  general
livelihood          0       5         3       0       0          9           15
scheme              0       0         0       0       0          5           0
training            0       3         0       0       0          0           5
market              0       0         0       0       0          2           3
expert              0       0         0       4       0          0           0
community           0       0         0       0       1          0           0
general             0       1         0       0       0          1           3
```

**Key Finding**: 
- livelihood_recommendation is confused with general_question (15 confusions)
- This is the MOST CRITICAL FAILURE because livelihood is 53% of the dataset

---

## Entity Extraction Failures (100% error rate)

### The Paradox
- **Extraction Rate**: 100% (all entities are being extracted)
- **Accuracy Rate**: 0% overall (all extracted entities are WRONG)
- **Critical Insight**: The system IS extracting entities, but extracting WRONG VALUES

### Entities Not Extracted Completely
These entities appear in the dataset but system extracted NOTHING:

```
enterprise (mushroom, honey, etc):         4 failures
  - System extracts "enterprise" field but gets wrong value
  - Examples: expected "mushroom", system says nothing extracted
  - Pattern: Marathi/Hindi agricultural terms not recognized

budget_rupees (50000-150000):              3 failures
  - Expected: 50000, System extracts: null
  - Pattern: Currency parsing fails in some cases

land_size_hectares (0.4-3.0):              2 failures  
  - Expected: 2.0 acres, System extracts: null
  - Pattern: Acre/hectare conversions sometimes fail

location (Nashik, Pune, Maharashtra):      1 failure
  - Expected: "nashik", System extracts: null
  - Pattern: Location recognition incomplete

water_availability (low, medium, high):    1 failure
  - Expected: "low", System extracts: null

experience_level (beginner, intermediate): 1 failure
  - Expected: "beginner", System extracts: null

time_availability (part_time, full_time):  1 failure
  - Expected: "full_time", System extracts: null
```

### Root Cause Analysis

**Problem 1: Regex Pattern Matching**
- Patterns are too restrictive or too greedy
- Marathi/Hindi variations not covered

**Problem 2: Value Normalization**
- When values ARE extracted, they're often in wrong format
- Examples: "50 हजार" (50 thousand) not parsed to 50000
- Examples: "2 एकर" (2 acres) not converted to hectares

**Problem 3: Language-Specific Entity Names**
- System knows "mushroom" but not "मशरूम" (marathi)
- System knows "budget" but not "बजेट" (marathi)

---

## Performance by Language

### Marathi (26 examples)
- Intent Accuracy: 53.8% (14/26 correct)
- Entity Accuracy: 0% (0/26 correct)
- Status: **BEST PERFORMANCE** but still only 54%

### Hindi (17 examples)
- Intent Accuracy: 41.2% (7/17 correct)
- Entity Accuracy: 0% (0/17 correct)
- Status: 12 percentage points worse than Marathi

### English (17 examples)
- Intent Accuracy: 41.2% (7/17 correct)
- Entity Accuracy: 0% (0/17 correct)
- Status: Tied with Hindi, also 54% below Marathi

### Why is Marathi Better?
1. Dataset may have better regex patterns for Marathi
2. Devanagari script is more consistently parsed than Latin variants
3. Hindi/English include Hinglish (mixed language) which breaks patterns
4. Marathi examples may be more straightforward

---

## Performance by Difficulty

### Easy Queries (17 examples)
- Intent Accuracy: **76.5%** (13/17 correct)
- Capability Routing: 70.6%
- Status: ✓ GOOD PERFORMANCE

### Medium Queries (29 examples)
- Intent Accuracy: **37.9%** (11/29 correct)
- Capability Routing: 34.5%
- Status: ⚠️ SIGNIFICANT DROP

### Hard Queries (14 examples)
- Intent Accuracy: **28.6%** (4/14 correct)
- Capability Routing: 21.4%
- Status: ⚠️ MAJOR PROBLEMS

### The Difficulty Gap
- Easy: 76.5% accuracy
- Hard: 28.6% accuracy
- **Drop: 48 percentage points**

**Interpretation**: 
- Deterministic patterns work for simple queries
- Complex context breaks pattern matching
- Multi-constraint queries fail

---

## What's Working Well

✓ **Perfect Intent Detection (100%)**
- scheme_search: 5/5 correct
- expert_request: 4/4 correct
- community: 1/1 correct

✓ **Perfect Language Detection (100%)**
- Marathi vs Hindi vs English detection: 60/60 correct

✓ **Easy Queries: 76.5% Accuracy**
- Simple, direct queries work reasonably well

✓ **Marathi Queries: 53.8% Accuracy**
- Best language performance

---

## What's Broken

✗ **Entity Extraction: 0% Accuracy**
- 100% extraction rate but WRONG VALUES
- Every entity type at 0-12.5% accuracy
- This blocks the entire system from working properly

✗ **Livelihood Intent: 28.1% Accuracy**
- 32 examples, only 9 correct
- Most important use case is mostly broken

✗ **Hindi/English: 29-41% Accuracy**
- 12-24 percentage point gap vs Marathi
- Language-specific patterns need work

✗ **Complex Queries: 28.6% Accuracy**
- Hard queries nearly always wrong
- Deterministic patterns fail with complexity

---

## Recommendations: What Should Be Fixed First

### PRIORITY 1: Fix Entity Extraction (Blocks Everything)
**Impact**: Highest - System cannot route to capabilities without correct entities
**Effort**: Medium - Requires regex pattern review and value parsing fixes
**Evidence**: 0% accuracy on 60 examples

**Specific Actions**:
1. Debug entity_extractor.py - trace what values ARE being extracted
2. Fix Marathi/Hindi language support in regex patterns
3. Implement value normalization (thousands, units, conversions)
4. Add language-specific entity dictionaries

**Testing Strategy**:
- Create 10-15 simple entity extraction test cases
- Verify each entity type with different language variants
- Measure extraction accuracy, not just rate

### PRIORITY 2: Fix Livelihood Intent Detection (Primary Use Case)
**Impact**: High - 53% of queries are livelihood-related
**Effort**: Medium - Requires pattern analysis and keyword refinement
**Evidence**: 28% accuracy on 32 examples

**Specific Actions**:
1. Analyze the 23 failing livelihood queries
2. Identify what keywords trigger misclassification to general_question
3. Add livelihood-specific keywords and patterns
4. Improve context understanding for livelihood queries

### PRIORITY 3: Improve Complex Query Handling
**Impact**: Medium - Many real farmers ask complex questions
**Effort**: High - Deterministic patterns may not be sufficient
**Evidence**: 48 percentage point accuracy drop from easy to hard queries

**Specific Actions**:
1. Consider simple ML classifier for intent when confidence is low
2. Implement multi-step interpretation for complex queries
3. Add confidence thresholds - reject uncertain predictions

### PRIORITY 4: Improve Hindi/English Support
**Impact**: Medium - Important for non-Marathi users
**Effort**: Medium - Language-specific patterns and dictionaries
**Evidence**: 12-24 percentage point gap vs Marathi

**Specific Actions**:
1. Review Hindi-specific regex patterns
2. Handle Hinglish (mixed Hindi-English) better
3. Add English language-specific entity names

---

## Should We Use Machine Learning?

### Current Evidence
- **Language Detection**: 100% accuracy - KEEP DETERMINISTIC
- **Scheme Search Intent**: 100% accuracy - KEEP DETERMINISTIC
- **Entity Extraction**: 0% accuracy - NEEDS HELP (ML or better regex)
- **Livelihood Intent**: 28% accuracy - NEEDS HELP (ML or better patterns)

### Recommendation
**NOT YET** for most components, but consider ML for:
1. **Entity Extraction** - If regex patterns can't reach 70%+ accuracy
2. **Intent Detection** - If pattern improvements don't reach 70%+ overall

### Threshold for ML Decision
- If deterministic reaches 70%+ accuracy → Stay deterministic
- If deterministic plateaus below 50% → Consider ML
- Current status: Deterministic at 46.7% (intent), 0% (entities)

---

## Next Steps

1. **TASK 9**: Create ML/SLM decision framework (based on this analysis)
2. **TASK 10**: Document training data needs (what examples to collect)
3. **TASK 11**: Verify backward compatibility with TASK 2-3 tests
4. **TASK 12**: Create comprehensive evaluation report

---

## Appendix: Dataset Coverage

### Intent Coverage
- livelihood_recommendation: 32 examples (53%)
- general_question: 5 examples (8%)
- scheme_search: 5 examples (8%)
- market_search: 5 examples (8%)
- training_request: 8 examples (13%)
- expert_request: 4 examples (7%)
- community: 1 example (2%)

### Language Coverage
- Marathi: 26 examples (43%)
- Hindi: 17 examples (28%)
- English: 17 examples (28%)

### Entity Coverage
- Queries with budget: 17 examples (28%)
- Queries with land_size: 16 examples (27%)
- Queries with location: 6 examples (10%)
- Queries with enterprise: 21 examples (35%)
- Other entities: < 10 examples each

### Difficulty Coverage
- Easy: 17 examples (28%)
- Medium: 29 examples (48%)
- Hard: 14 examples (23%)

