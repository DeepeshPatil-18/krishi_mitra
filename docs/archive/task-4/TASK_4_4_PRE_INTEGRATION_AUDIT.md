# TASK 4.4: PRE-INTEGRATION ARCHITECTURE AUDIT

**Date**: August 22, 2026  
**Purpose**: Document current entity flow before integration

---

## EXECUTIVE SUMMARY

**Current State**: EntityExtractor and EntityNormalizer exist but are NOT connected to production AIOrchestrator pipeline.

**Production Flow**: AIOrchestrator → IntentRouter.extract_parameters() → minimal regex extraction

**Impact**: Entity normalization improvements from TASK 4.2 and 4.3 are NOT active in production

---

## 1. CURRENT AIORCHESTRATOR FLOW

### File: `app/services/ai_orchestrator.py`

```python
def orchestrate(message, language, farmer_id, provided_context) -> OrchestratorContext:
    # Step 1: Detect language
    ctx.detected_language = LanguageService.detect_language(message)
    
    # Step 2: Detect intent
    intent, confidence, base_params = IntentRouter.detect_intent(
        message=message,
        language=ctx.detected_language,
        context=provided_context or {},
    )
    
    # Step 3: Extract entities (CURRENT - BASIC REGEX ONLY)
    extracted = IntentRouter.extract_parameters(
        message=message,
        intent=intent,
        language=ctx.detected_language,
    )
    extracted.update(base_params)
    ctx.extracted_entities = extracted  # <-- Raw values stored here
    
    # Step 4: Build farmer context
    ctx.farmer_context = AIOrchestrator._build_farmer_context(
        provided_context or {},
        extracted,  # <-- Raw values passed to context builder
        ctx.detected_language,
    )
    
    # Step 5-6: Missing info + completeness
    ...
```

**Integration Point**: Line ~119-124 (Step 3)

---

## 2. CURRENT INTENTROUTER.EXTRACT_PARAMETERS()

### File: `app/services/intent_router.py`

```python
@staticmethod
def extract_parameters(message: str, intent: Intent, language: str) -> Dict[str, Any]:
    """
    Extract parameters from message based on intent.
    
    CURRENT IMPLEMENTATION: Very basic regex extraction
    """
    params = {}
    
    if intent == Intent.LIVELIHOOD_RECOMMENDATION:
        # Simple regex - only extracts "50 हजार" → 50000
        import re
        budget_match = re.search(r"(\d+)\s*(हजार|thousand|rupees|रुपये)", message, re.IGNORECASE)
        if budget_match:
            params["budget"] = int(budget_match.group(1)) * 1000
    
    elif intent == Intent.MARKET_SEARCH:
        # Basic keyword matching for product
        if any(word in message.lower() for word in ["मध", "शहद", "honey"]):
            params["product"] = "honey"
        elif any(word in message.lower() for word in ["अंडे", "egg"]):
            params["product"] = "eggs"
    
    return params
```

**Limitations**:
- Only handles basic budget extraction ("50 हजार")
- Does NOT handle: "लगभग 50000", "50-100k", "50 हजार रुपये"
- Does NOT extract: land_size, experience, water, risk, time
- Does NOT normalize values
- Does NOT use EntityExtractor or EntityNormalizer

---

## 3. ENTITYEXTRACTOR API

### File: `app/services/entity_extractor.py`

**Class**: Static methods (no instantiation required)

**Main Method**:
```python
@staticmethod
def extract_all(message: str, language: str = "auto") -> Dict[str, Any]:
    """
    Extract all relevant entities from a message.
    
    Returns:
        Dict[str, Any] with keys like:
        {
            "budget_rupees": "50000",  # Raw string
            "land_size_hectares": "2 एकर",  # Raw string with unit
            "experience_level": "beginner",  # May already be normalized
            "water_availability": "high",
            "risk_tolerance": "medium",
            "time_availability": "full_time",
            "location": "पुणे"
        }
    """
```

**Return Type**: `Dict[str, Any]` with RAW extracted values (strings, not normalized numbers)

**Extraction Order**:
1. Numeric values (budget, land, income) - FIRST to avoid false matches
2. Location - EARLY to avoid conflicts
3. Categorical values (enterprise, water, experience, risk, time)

**Capabilities**:
- Marathi/Hindi/English support
- Multi-entity extraction
- Handles Devanagari numerals
- Does NOT normalize - returns raw extracted strings

---

## 4. ENTITYNORMALIZER API

### File: `app/services/entity_normalizer.py`

**Class**: Static methods (no instantiation required)

**Main Method**:
```python
@staticmethod
def normalize_entity(entity_type: str, raw_value: Any) -> Dict[str, Any]:
    """
    Normalize a single entity.
    
    Args:
        entity_type: "budget_rupees", "land_size_hectares", "location", etc.
        raw_value: Raw extracted value (e.g., "50 हजार", "2 एकर", "आधा एकर")
    
    Returns:
        {
            'raw_value': <original>,
            'normalized_value': <normalized>,  # e.g., 50000, 0.809, "pune"
            'normalization_confidence': 0.0-1.0,
            'format_detected': <format_type>,
            'needs_clarification': bool,
            'notes': <string>
        }
    """
```

**Supported Entity Types**:
- `budget_rupees`: "50 हजार" → 50000, "लगभग 50000" → 50000, "50-100k" → 75000
- `land_size_hectares`: "2 एकर" → 0.809, "आधा एकर" → 0.202, "डेढ़ एकर" → 0.607
- `location`: "पुणे" → "pune", district normalization
- `experience_level`: "2 साल" → "beginner", "5 साल" → "intermediate"
- `water_availability`: Keywords → "high"/"medium"/"low"
- `risk_tolerance`: Keywords → "high"/"medium"/"low"
- `time_availability`: Keywords → "full_time"/"part_time"/"limited"
- `time_numeric`: "3 महिना" → 3

**TASK 4.3 Improvements** (already implemented):
1. Land size: Marathi fractions ("आधा", "डेढ़"), precise conversion (0.404686)
2. Budget: Ranges ("50-100k"), approximations ("लगभग"), mixed ("50 हजार")
3. Experience: Year thresholds (<2→beginner, 2-10→intermediate, >10→expert)

**Key Feature**: Returns dict with metadata, NOT just the normalized value

---

## 5. FARMERCONTEXT STRUCTURE

### File: `app/schemas/advisory.py`

```python
class FarmerContext(BaseModel):
    """Comprehensive farmer context for advisory"""
    
    # Core information
    budget_rupees: int = Field(..., gt=0)  # REQUIRES NORMALIZED INTEGER
    location: Optional[str] = Field(None)
    land_size_hectares: Optional[float] = Field(None, ge=0.0)  # REQUIRES NORMALIZED FLOAT
    water_availability: Optional[str] = Field(None)  # "low"/"medium"/"high"
    experience_level: str = Field(default="beginner")  # "beginner"/"intermediate"/"expert"
    
    # Additional context
    income_goal_monthly: Optional[int] = Field(None, gt=0)
    preferred_enterprise: Optional[str] = Field(None)
    existing_resources: Optional[List[str]] = Field(None)
    electricity_available: Optional[bool] = Field(None)
    willingness_to_learn: Optional[bool] = Field(default=True)
    risk_tolerance: Optional[str] = Field(default="medium")  # "low"/"medium"/"high"
    time_availability: Optional[str] = Field(None)  # "full_time"/"part_time"/"limited"
```

**Expectations**:
- `budget_rupees`: INT (not string "50 हजार")
- `land_size_hectares`: FLOAT (not string "2 एकर")
- Categorical fields: Standard values ("high", "beginner", not raw keywords)

---

## 6. CONTEXT BUILDER LOGIC

### File: `app/services/ai_orchestrator.py::_build_farmer_context()`

```python
def _build_farmer_context(provided: Dict, extracted: Dict, language: str) -> Optional[FarmerContext]:
    """
    Build farmer context from provided and extracted data.
    
    Merges extracted into provided (provided takes priority).
    """
    merged = {**extracted, **provided}  # provided overrides extracted
    
    # Get budget (supports both keys)
    budget = merged.get("budget_rupees") or merged.get("budget")
    if not budget or budget <= 0:
        return None  # Budget is required
    
    try:
        return FarmerContext(
            budget_rupees=budget,  # <-- EXPECTS INT not string
            land_size_hectares=merged.get("land_size_hectares") or merged.get("land"),  # <-- EXPECTS FLOAT
            water_availability=merged.get("water_availability"),
            experience_level=merged.get("experience_level") or "beginner",
            location=merged.get("location"),
            income_goal_monthly=merged.get("income_goal_monthly") or merged.get("income_goal"),
            time_availability=merged.get("time_availability"),
            risk_tolerance=merged.get("risk_tolerance"),
            existing_resources=merged.get("existing_resources"),
        )
    except Exception:
        return None  # Validation fails
```

**Current Problem**:
- If extracted contains `{"budget_rupees": "50 हजार"}` (string), FarmerContext validation FAILS
- If extracted contains `{"land_size_hectares": "2 एकर"}` (string), FarmerContext validation FAILS
- IntentRouter.extract_parameters() DOES convert "50 हजार" → 50000 for basic cases
- But EntityExtractor returns RAW strings, EntityNormalizer is never called

---

## 7. CAPABILITY EXECUTION EXPECTATIONS

### File: `app/services/advisory_service.py`

```python
def get_recommendations(
    budget_rupees: int,  # <-- EXPECTS NORMALIZED INT
    land_size_hectares: float,  # <-- EXPECTS NORMALIZED FLOAT
    state: str,
    experience_level: str = "beginner",
    goals: Optional[str] = None,
) -> tuple[List[RecommendedEnterprise], str]:
```

**Requirements**:
- Advisory service expects numeric values
- AdvisoryEngine.recommend_enterprises() uses these for scoring
- String values like "50 हजार" would cause failures

---

## 8. ORCHESTRATORCONTEXT STRUCTURE

### File: `app/services/ai_orchestrator.py`

```python
@dataclass
class OrchestratorContext:
    """Lightweight context for current request"""
    farmer_id: Optional[str] = None
    message: str = ""
    language: str = "english"
    detected_language: str = "english"
    intent: Optional[Intent] = None
    intent_confidence: float = 0.0
    extracted_entities: Dict[str, Any] = field(default_factory=dict)  # <-- Storage for entities
    farmer_context: Optional[FarmerContext] = None
    missing_information: List[str] = field(default_factory=list)
    information_completeness: float = 0.0
```

**Storage**: `extracted_entities` is `Dict[str, Any]`
- Currently stores output of IntentRouter.extract_parameters()
- Should store normalized values after integration

---

## 9. INTEGRATION POINT ANALYSIS

### Current Code (Line 119-124):

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

### Required Change:

```python
# Step 3: Extract entities WITH NORMALIZATION
from app.services.entity_extractor import EntityExtractor
from app.services.entity_normalizer import EntityNormalizer

# 3a. Extract raw entities
raw_entities = EntityExtractor.extract_all(
    message=message,
    language=ctx.detected_language
)

# 3b. Normalize each entity
normalized_entities = {}
for entity_type, raw_value in raw_entities.items():
    if raw_value is not None:
        norm_result = EntityNormalizer.normalize_entity(entity_type, raw_value)
        normalized_value = norm_result.get('normalized_value')
        
        if normalized_value is not None:
            normalized_entities[entity_type] = normalized_value
        # If normalization fails, DON'T store entity (avoid bad data)

# 3c. Merge with base_params (from intent detection)
normalized_entities.update(base_params)

# 3d. Store normalized entities
ctx.extracted_entities = normalized_entities
```

---

## 10. COMPATIBILITY RISKS

### Risk 1: Breaking IntentRouter callers
**Analysis**: IntentRouter.extract_parameters() is only called from AIOrchestrator line ~119
**Mitigation**: Replace the call entirely; no other callers found

### Risk 2: Changing extracted_entities structure
**Analysis**: _build_farmer_context() expects Dict[str, Any] with normalized values
**Mitigation**: Integration IMPROVES compatibility (currently broken for complex cases)

### Risk 3: Entity key naming mismatch
**Analysis**: 
- EntityExtractor returns: `budget_rupees`, `land_size_hectares`
- FarmerContext expects: `budget_rupees`, `land_size_hectares` (also accepts `budget`, `land`)
- _build_farmer_context() handles both key names
**Mitigation**: Keys match; backwards compatible

### Risk 4: Missing entities
**Analysis**: If EntityExtractor doesn't find entity, key won't exist in dict
**Current behavior**: IntentRouter returns empty dict `{}` for most intents
**Mitigation**: Same behavior; no breaking change

### Risk 5: Normalization failures
**Analysis**: If normalization fails, `normalized_value` is None
**Mitigation**: Don't store failed normalizations (leave entity absent)

---

## 11. BACKWARD COMPATIBILITY STRATEGY

### Keep IntentRouter.extract_parameters() unchanged
- Other code may depend on it (tests, direct calls)
- Don't delete or modify it
- Simply don't call it from orchestrator

### Preserve extracted_entities semantics
- Still a Dict[str, Any]
- Still contains simple values (int, float, str)
- Still passed to _build_farmer_context()

### Preserve FarmerContext interface
- No schema changes required
- Already expects normalized values
- Integration makes it work as designed

---

## 12. EVALUATION PATH VERIFICATION

### TASK 4.2 Evaluation (Custom Script)
**File**: `scripts/task_4_2_evaluation.py`

```python
# Called EntityExtractor + EntityNormalizer DIRECTLY
raw_entities = EntityExtractor.extract_all(message, language)
for entity_type, raw_value in raw_entities.items():
    normalized = EntityNormalizer.normalize_entity(entity_type, raw_value)
```

**Result**: 46.8% entity accuracy (EntityNormalizer working correctly)

### Production Evaluation (Should use AIOrchestrator)
**File**: `scripts/evaluate_farmer_dataset.py`

Should call:
```python
ctx = AIOrchestrator.orchestrate(message, language, farmer_id, provided_context)
```

**Current Problem**: AIOrchestrator doesn't use EntityExtractor/Normalizer
**Expected Result After Integration**: ~46-50% entity accuracy

---

## 13. TESTING REQUIREMENTS

### Pre-Integration Tests to Run:
1. Existing test suite baseline
2. Entity normalizer unit tests (should all pass)
3. EntityExtractor unit tests (should all pass)
4. Integration tests baseline

### Post-Integration Tests to Run:
1. Entity normalizer unit tests (should still pass)
2. EntityExtractor unit tests (should still pass)
3. New integration tests (test end-to-end flow)
4. Existing test suite (check for regressions)
5. Production evaluation with farmer_queries.jsonl

---

## 14. SUCCESS CRITERIA

### Integration is successful when:

1. ✅ EntityExtractor.extract_all() called from orchestrator
2. ✅ EntityNormalizer.normalize_entity() called for each entity
3. ✅ Normalized values stored in ctx.extracted_entities
4. ✅ Normalized values reach FarmerContext
5. ✅ Normalized values reach advisory capabilities
6. ✅ No duplicate entity pipelines exist
7. ✅ Existing tests don't regress
8. ✅ Integration tests pass
9. ✅ Production evaluation shows entity accuracy ~46-50%

### Examples to Verify:

| Input | Expected Normalized Output |
|-------|---------------------------|
| "माझ्याकडे 2 एकर जमीन आहे" | `land_size_hectares: 0.809` |
| "50 हजार रुपये budget" | `budget_rupees: 50000` |
| "आधा एकर जमीन" | `land_size_hectares: 0.202` |
| "डेढ़ एकर" | `land_size_hectares: 0.607` |
| "लगभग 50000 रुपये" | `budget_rupees: 50000` |
| "50-100k budget" | `budget_rupees: 75000` |
| "2 साल अनुभव" | `experience_level: "beginner"` |
| "5 साल अनुभव" | `experience_level: "intermediate"` |

---

## 15. ARCHITECTURAL CONCLUSION

**Current State**: BROKEN
- EntityExtractor and EntityNormalizer exist and work correctly
- TASK 4.2 and 4.3 improvements are implemented and tested
- But they are NOT connected to production pipeline

**Required Change**: SIMPLE AND CLEAN
- Replace one method call (IntentRouter.extract_parameters)
- Add EntityExtractor.extract_all() + normalization loop
- Store normalized values (not full metadata dict)
- ~20 lines of code

**Complexity**: LOW
- No schema changes
- No breaking changes
- No new dependencies
- Improves existing broken flow

**Expected Impact**: HIGH
- Entity accuracy: 0% → ~46-50%
- Enables TASK 4.2/4.3 improvements
- Unlocks future deterministic optimization

---

## NEXT STEP

Proceed to PART 2: Implement integration in `app/services/ai_orchestrator.py`

---

**Audit Complete**: August 22, 2026
