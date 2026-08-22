# NEXT STEPS: CRITICAL ACTION REQUIRED

🚨 **BLOCKER IDENTIFIED**: EntityNormalizer not integrated into production orchestrator

---

## IMMEDIATE ACTION (Priority 1)

### Task: Integrate EntityNormalizer into AIOrchestrator
**Time Estimate**: 2-4 hours  
**Difficulty**: Medium  
**Impact**: HIGH - Unlocks 46.8% entity accuracy

### Step-by-Step Instructions

#### 1. Modify AIOrchestrator (app/services/ai_orchestrator.py)

**Current code** (around line 119):
```python
# Step 3: Extract entities
extracted = IntentRouter.extract_parameters(
    message=message,
    intent=intent,
    language=ctx.detected_language,
)
extracted.update(base_params)
ctx.extracted_entities = extracted
```

**Replace with**:
```python
# Step 3: Extract entities (WITH NORMALIZATION)
from app.services.entity_extractor import EntityExtractor
from app.services.entity_normalizer import EntityNormalizer

# Extract raw entities
extracted_raw = EntityExtractor.extract_all(
    message=message,
    language=ctx.detected_language
)

# Normalize each entity
normalized_entities = {}
for entity_type, raw_value in extracted_raw.items():
    normalization_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
    normalized_value = normalization_result.get('normalized_value')
    if normalized_value is not None:
        normalized_entities[entity_type] = normalized_value

# Merge with base_params (from IntentRouter)
normalized_entities.update(base_params)
ctx.extracted_entities = normalized_entities
```

#### 2. Test the Integration

Run the evaluation:
```bash
cd d:\krishimitra_backend
python scripts/evaluate_farmer_dataset.py
```

**Expected results**:
- Entity accuracy should jump from ~0% to ~47-50%
- Intent accuracy should remain at 61.7%
- No regressions in language or capability routing

#### 3. Verify TASK 4.3 Improvements

Run the unit tests:
```bash
python test_entity_fixes.py
```

All 24 tests should still pass.

Run integration test:
```bash
python test_improvement.py
```

Entity accuracy should now show improvement instead of 0%.

#### 4. Document Results

Update these files with actual results:
- `data/evaluation/task_4_3_after_integration.json` (create this)
- Add section to `TASK_4_3_FINAL_REPORT.md` documenting integration results

---

## AFTER INTEGRATION (Priority 2)

### If Entity Accuracy 47-50% (improvement ≥ 2%)
✅ **Continue deterministic approach**
- Implement location mapping (if needed)
- Add more unit conversions
- Complete TASK 4.3 Parts 8-11

### If Entity Accuracy 46.8-49% (improvement < 2%)
⚠️ **Plateau detected**
- Perform semantic gap assessment
- Identify which failures are semantic vs pattern-based
- Consider hybrid approach (deterministic + ML for semantic cases)

### If Entity Accuracy < 46.8%
❌ **Regression detected**
- Debug integration
- Check evaluation script is using orchestrator correctly
- Verify EntityExtractor and EntityNormalizer are working

---

## FILES TO READ

### Understanding the Issue
1. **TASK_4_3_SUMMARY.txt** - Quick overview (2 min read)
2. **TASK_4_3_FINAL_REPORT.md** - Full details (15 min read)
   - See "PART 7: CRITICAL ARCHITECTURAL ISSUE DISCOVERED"

### Code to Review
1. **app/services/entity_normalizer.py** - The normalizer (already improved)
2. **app/services/ai_orchestrator.py** - Needs modification (line ~119)
3. **app/services/entity_extractor.py** - Extract raw entities
4. **scripts/evaluate_farmer_dataset.py** - Evaluation script

### Tests
1. **test_entity_fixes.py** - Unit tests (24/24 passing)
2. **test_improvement.py** - Integration test (currently shows 0% due to bug)

---

## VERIFICATION CHECKLIST

Before marking integration complete:

- [ ] Modified AIOrchestrator.orchestrate() to use EntityExtractor + EntityNormalizer
- [ ] Ran evaluate_farmer_dataset.py - entity accuracy ≥ 45%
- [ ] Ran test_entity_fixes.py - all 24 tests pass
- [ ] Ran test_improvement.py - shows improvement not 0%
- [ ] No regression in intent accuracy (should stay ~61.7%)
- [ ] No regression in language detection (should stay ~71.7%)
- [ ] Created task_4_3_after_integration.json with results
- [ ] Updated TASK_4_3_FINAL_REPORT.md with integration section

---

## WHY THIS MATTERS

**Current State**:
- EntityNormalizer has excellent improvements (24/24 tests passing)
- But it's NOT called by the production orchestrator
- Production entity accuracy likely 0%
- All TASK 4.2 and 4.3 improvements are disconnected

**After Integration**:
- Production will use EntityNormalizer
- Entity accuracy should jump to ~47-50%
- TASK 4.3 improvements will be active
- Can continue with more optimizations

**Impact**:
- Farmers will get better recommendations (accurate budget/land/experience parsing)
- Livelihood recommendations will be more personalized
- System will understand "50 हजार", "आधा एकर", etc.

---

## QUESTIONS?

See these files for more information:
- **TASK_4_INDEX.md** - Navigation guide for all TASK 4 deliverables
- **TASK_4_3_FINAL_REPORT.md** - Comprehensive technical report
- **TASK_4_3_SUMMARY.txt** - Quick reference

---

**Created**: August 22, 2026  
**Status**: URGENT - Architecture blocker preventing progress  
**Assigned**: Next developer working on KrishiMitra backend
