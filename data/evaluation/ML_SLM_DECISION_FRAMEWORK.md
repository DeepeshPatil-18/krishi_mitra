# ML/SLM Decision Framework - KrishiMitra

**Date**: August 19, 2026  
**Based on**: Baseline evaluation (60 queries) and detailed error analysis  
**Status**: EVIDENCE-BASED RECOMMENDATIONS (not final implementation)

---

## Framework Overview

This document evaluates each KrishiMitra component and recommends whether to:
- **Keep Deterministic**: Current rule-based/regex approach is sufficient
- **Improve Deterministic**: Add more patterns, rules, or heuristics
- **Use ML**: Train a classifier on examples
- **Use SLM**: Use a Small Language Model for interpretation
- **Use API**: Call external service
- **Hybrid**: Combine approaches

**Key Principle**: Only recommend ML/SLM if deterministic has evidence of failure.

---

## Component-by-Component Analysis

### 1. Language Detection

**Current Accuracy**: 100% (60/60 correct)

**Deterministic Method**: 
- Detects Devanagari script (Marathi/Hindi) vs Latin (English)
- Simple Unicode range check

**Evidence**:
- Perfect performance on all 60 examples
- Works across all languages and difficulties
- No failures observed

**Recommendation**: ✓ **KEEP DETERMINISTIC**

**Rationale**: 
- 100% accuracy cannot be improved
- Rule-based approach is simple and reliable
- No need for ML

**Cost of ML**: Would actually make this worse (adds latency, complexity)

---

### 2. Intent Detection (Routing)

**Current Accuracy**: 46.7% (28/60 correct)

**Deterministic Method**: 
- Keyword matching and regex patterns
- Intent-specific pattern dictionaries

**Evidence**:

| Intent | Examples | Accuracy | Status |
|--------|----------|----------|--------|
| scheme_search | 5 | 100% | ✓ Excellent |
| expert_request | 4 | 100% | ✓ Excellent |
| community | 1 | 100% | ✓ Excellent |
| market_search | 5 | 60% | ⚠️ Acceptable |
| general_question | 5 | 60% | ⚠️ Acceptable |
| training_request | 8 | 37.5% | ✗ Poor |
| livelihood_recommendation | 32 | 28.1% | ✗ Critical Failure |

**By Language**:
- Marathi: 53.8% accuracy
- Hindi: 41.2% accuracy
- English: 41.2% accuracy

**By Difficulty**:
- Easy: 76.5% accuracy ✓
- Medium: 37.9% accuracy ⚠️
- Hard: 28.6% accuracy ✗

**Recommendation**: ⚠️ **IMPROVE DETERMINISTIC FIRST, THEN EVALUATE ML**

**Rationale**:
1. 46.7% is below acceptable (target: 70%+)
2. But some intents work perfectly (scheme_search 100%)
3. Suggests patterns can be improved before ML
4. Evidence shows complexity breaks patterns (easy 77% → hard 29%)

**Short-term Actions** (Do this BEFORE ML):
1. Add more keywords for livelihood_recommendation
2. Improve context analysis for complex queries
3. Add language-specific patterns for Hindi/English
4. Increase confidence thresholds for uncertain cases

**ML Trigger Threshold**:
- If deterministic improves to 60%+: Stay deterministic
- If deterministic plateaus below 55%: Evaluate ML
- If deterministic reaches 70%+: Keep deterministic

**ML Approach (if needed)**:
- Supervised classifier: Intent classifier trained on labeled farmer queries
- Training data needed: 200-500 diverse examples (current: 60)
- Model type: Text classification (could use fine-tuned SLM or simple classifier)
- Confidence thresholds: Reject low-confidence predictions

---

### 3. Entity Extraction

**Current Accuracy**: 0% (0/60 entities correct overall)

**Extraction Rate**: 100% (entities ARE being extracted)

**Deterministic Method**:
- Regex patterns per entity type
- Value parsing and normalization

**Entity-Level Evidence**:

| Entity | Expected | Extraction Rate | Accuracy | Status |
|--------|----------|-----------------|----------|--------|
| budget_rupees | 17 | 100% | 0% | ✗ Completely Wrong |
| land_size_hectares | 16 | 100% | 12.5% | ✗ Mostly Wrong |
| location | 6 | 100% | 0% | ✗ Completely Wrong |
| enterprise | 21 | 100% | 0% | ✗ Completely Wrong |
| water_availability | 6 | 100% | 0% | ✗ Completely Wrong |
| experience_level | 6 | 100% | 0% | ✗ Completely Wrong |
| time_availability | 3 | 100% | 0% | ✗ Completely Wrong |
| willingness_to_learn | 2 | 100% | 0% | ✗ Completely Wrong |
| risk_tolerance | 1 | 100% | 0% | ✗ Completely Wrong |

**Key Paradox**:
- System extracts SOMETHING for every entity (100% rate)
- But extracts WRONG things (0% accuracy)
- This is NOT a "missing data" problem
- This is a "WRONG VALUE" problem

**Failure Mode Analysis**:
- Expected: "50000 rupees" → Got: null (NOT extracted correctly)
- Expected: "mushroom" → Got: null (enterprise value missing)
- Expected: "nashik" → Got: null (location not found)
- Expected: "1.5 hectares" → Got: null (land size not parsed)

**Root Causes**:
1. **Regex Patterns Too Restrictive**
   - Patterns don't match Marathi/Hindi text
   - Example: Looking for "rupees" but text says "रुपये"

2. **Value Parsing Issues**
   - "50 हजार" (50 thousand) not parsed to 50000
   - "2 एकर" (2 acres) not converted correctly

3. **Dictionary/Keyword Misses**
   - Location names incomplete
   - Enterprise types incomplete

**Recommendation**: 🚨 **NEEDS SIGNIFICANT WORK**

### Assessment: Deterministic vs ML

**Can Deterministic Be Fixed?**
- YES, partially
- Root causes are known (regex, parsing, dictionaries)
- Can likely reach 60-70% accuracy with fixes

**Should We Use ML for Entity Extraction?**

| Approach | Pros | Cons | Timeline |
|----------|------|------|----------|
| **Fix Deterministic** | Simple, interpretable, fast | Limited ceiling | 1-2 weeks |
| **ML Classification** | Higher accuracy potential | Requires training data | 2-4 weeks |
| **SLM Extraction** | Good at context | Higher latency, cost | 1-2 weeks |
| **Hybrid** | Best accuracy + speed | More complex | 3-4 weeks |

**Recommendation**: **USE HYBRID APPROACH**

**Phase 1** (Week 1-2): Fix deterministic patterns
- Goal: Reach 60-70% accuracy
- Action: Improve regex, add dictionaries, fix parsing

**Phase 2** (Week 2-3): Evaluate SLM if needed
- Use small model (e.g., Llama 2 7B locally)
- Test on 30 examples
- If 85%+ accuracy: Implement SLM
- If <80% accuracy: Stick with deterministic

**Phase 2 Alternative** (Week 2-3): Train ML classifier
- Use labeled extraction examples
- Collect 200-300 training examples
- Train sequence labeling model (NER style)
- If 80%+ accuracy: Implement ML
- If <70% accuracy: Stick with deterministic

**Why Hybrid?**
1. Deterministic handles simple cases fast (no latency)
2. ML/SLM handles complex cases accurately
3. Fallback when either approach fails

---

### 4. Capability Routing

**Current Accuracy**: 41.7% (25/60 correct)

**Deterministic Method**:
- Maps intent → capability handler
- Intent: scheme_search → Capability: scheme_search_handler
- Intent: livelihood_recommendation → Capability: advisory_handler

**Evidence**:
- Fails exactly when intent detection fails
- When intent is correct (scheme_search 100%), routing is 100% correct
- Failures are INHERITED from intent detection failures

**Recommendation**: ✓ **KEEP DETERMINISTIC** (Fix intent first)

**Rationale**:
- Capability routing is deterministic mapping
- Failures are caused by intent detection errors, not routing
- Fixing intent detection will fix capability routing

**Action**: No changes needed until intent detection is improved

---

## Summary Table

| Component | Current Accuracy | Status | Recommendation | Target Accuracy | Effort |
|-----------|------------------|--------|-----------------|-----------------|--------|
| Language Detection | 100% | ✓ Excellent | Keep Deterministic | 100% | None |
| Intent Detection | 46.7% | ✗ Poor | Improve Deterministic → ML | 70%+ | Medium → High |
| Entity Extraction | 0% | ✗ Critical | Improve Deterministic → Hybrid | 70%+ | High → Very High |
| Capability Routing | 41.7% | ✗ Poor (Inherited) | Keep Deterministic | 70%+ | Low (Fix Intent) |

---

## Phased Implementation Plan

### Phase 1: Improve Deterministic (Weeks 1-2)

**Goal**: Reach 60%+ accuracy before considering ML

**Intent Detection Improvements**:
1. Add livelihood-specific keyword dictionary (most important use case)
2. Improve context analysis for complex queries (easy→hard gap)
3. Add Hindi/English language-specific patterns
4. Implement confidence thresholds - reject uncertain predictions

**Entity Extraction Improvements**:
1. Fix regex patterns for Marathi/Hindi entities
2. Add value normalization (currency, units, conversions)
3. Expand enterprise and location dictionaries
4. Fix language-specific entity names

**Success Criteria**:
- Intent detection: 60%+ accuracy
- Entity extraction: 50%+ accuracy
- No regressions on currently-working intents (scheme_search, expert_request)

**Testing**:
- Re-evaluate on same 60-query dataset
- Must show measurable improvement
- Run TASK 2-3 tests for backward compatibility

### Phase 2: ML/SLM Evaluation (Weeks 2-3, only if Phase 1 doesn't reach 70%)

**If Intent Detection < 70% accuracy**:
1. Collect additional 200-300 labeled examples
2. Train text classification model
3. Test against held-out set
4. If 80%+ accuracy: Implement

**If Entity Extraction < 70% accuracy**:
1. Collect 200-300 labeled extraction examples
2. Train sequence labeling model (NER style)
3. Test on Marathi, Hindi, English subsets
4. If 80%+ accuracy: Implement

**If Both < 70% accuracy**:
1. Consider SLM approach (locally-run, no API calls)
2. Test fine-tuned Llama or similar small model
3. Balance accuracy vs latency vs cost

### Phase 3: Integration & Testing (Weeks 3-4)

**Integration**:
- Update AI Orchestrator to use new models
- Add confidence tracking and fallbacks
- Log model decisions for analysis

**Testing**:
- Run evaluation on 60-query dataset
- Compare before/after accuracy
- Measure latency (deterministic vs ML/SLM)
- Run full test suite (TASK 2-3 compatibility)

**Deployment**:
- Update baseline metrics
- Document model versions and training data
- Set up monitoring for model performance

---

## Training Data Specification (For ML/SLM)

### If Intent Detection Needs ML

**Format**: JSON lines (JSONL)
```json
{
  "text": "मी 50000 रुपये आणि 2 एकर जमीन आहे. मशरूम शेती सुरू करू शकते का?",
  "intent": "livelihood_recommendation",
  "language": "marathi",
  "difficulty": "medium"
}
```

**Size**: 200-500 examples
**Distribution**:
- livelihood_recommendation: 150+ (most important)
- training_request: 50+ (currently poor)
- Others: 50+ mixed (to maintain balance)

### If Entity Extraction Needs ML

**Format**: JSON lines with entity spans
```json
{
  "text": "मी 50000 रुपये आणि 2 एकर जमीन आहे",
  "entities": [
    {"type": "budget_rupees", "value": 50000, "span": [2, 10]},
    {"type": "land_size_hectares", "value": 0.81, "span": [14, 20]}
  ],
  "language": "marathi"
}
```

**Size**: 200-300 examples
**Coverage**: All 9 entity types across all 3 languages

---

## Cost-Benefit Analysis

| Approach | Implementation Cost | Runtime Cost | Accuracy | When to Use |
|----------|-------------------|--------------|----------|------------|
| Deterministic | Low | Low | 46-60% | Phase 1, simple queries |
| ML Classifier | Medium | Low | 65-80% | If deterministic plateaus |
| SLM (Llama 7B) | Medium | Medium | 75-85% | If local deployment possible |
| API SLM (Claude) | Low (API cost) | High | 90%+ | If accuracy critical, cost OK |
| Hybrid | High | Medium | 80-90% | Long-term, best balance |

---

## Risks & Mitigations

### Risk 1: ML Model Overfits to Evaluation Dataset
**Mitigation**: Hold out 10-20% of evaluation data for testing

### Risk 2: ML Model Fails on Different User Input Patterns
**Mitigation**: Collect diverse examples from multiple regions, demographics

### Risk 3: Latency Regression (ML models slower than deterministic)
**Mitigation**: Test latency requirements, consider model size, implement caching

### Risk 4: Dependency on External ML Infrastructure
**Mitigation**: Use locally-run models (avoid cloud APIs), keep deterministic as fallback

### Risk 5: Training Data Collection Takes Too Long
**Mitigation**: Use deterministic with lower confidence thresholds while collecting data

---

## Conclusion

**Immediate Action (Next 1-2 Weeks)**:
1. DO NOT implement ML yet
2. DO improve deterministic patterns (high ROI)
3. DO collect more evaluation examples during improvement
4. DO measure incremental progress

**Decision Point (End of Week 2)**:
- If deterministic reaches 70%+: Stay deterministic
- If deterministic plateaus at 50-70%: Evaluate ML
- If deterministic fails catastrophically (<50%): Implement ML

**Conservative Approach**: 
- Phase 1 improvements will likely reach 60-70% accuracy
- This may be "good enough" for MVP
- Full ML solution can be added later with better training data

**Aggressive Approach**:
- Start collecting training data now (parallel to Phase 1)
- Have ML models ready by end of Week 2
- Switch to ML if Phase 1 doesn't deliver 70%+

---

## Next Steps

1. **Implement Phase 1 improvements** (deterministic fixes)
2. **Re-run evaluation** with improved code
3. **Decide on ML/SLM** based on Phase 1 results
4. **Document training data** needs (in TASK 10)
5. **Verify backward compatibility** (TASK 11)

