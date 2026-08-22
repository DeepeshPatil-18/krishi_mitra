# Training Data Specification - KrishiMitra

**Date**: August 19, 2026  
**Purpose**: Define structure for future training data (IF ML/SLM is implemented)  
**Status**: SPECIFICATION ONLY - NO DATA CREATED YET  
**Key Constraint**: DO NOT create fake/synthetic training data

---

## Overview

This document specifies the format and requirements for training data if ML or SLM approaches are chosen for:
1. Intent detection/routing
2. Entity extraction
3. Other future components

**Important**: This spec is a PLAN, not an implementation. Training data must be collected from real farmer interactions, not generated synthetically.

---

## 1. Intent Detection Training Data

### Purpose
Train ML classifier to detect farmer intent from natural language queries across Marathi, Hindi, and English.

### Format: JSONL (JSON Lines)

```json
{
  "id": "train_intent_001",
  "text": "मी 50000 रुपये आणि 2 एकर जमीन आहे. कोणत्या शेतीच्या व्यवसायात हाती घालू?",
  "language": "marathi",
  "intent": "livelihood_recommendation",
  "difficulty": "medium",
  "source": "farmer_feedback_2026_08",
  "notes": "Multiple entities mentioned, asking for recommendation"
}
```

### Required Fields

| Field | Type | Values | Required | Notes |
|-------|------|--------|----------|-------|
| id | string | unique identifier | Yes | Format: `train_intent_<number>` |
| text | string | farmer query | Yes | Original text, NOT translated |
| language | string | `marathi`, `hindi`, `english`, `mixed` | Yes | Actual language of text |
| intent | string | See intent list below | Yes | Ground truth intent |
| difficulty | string | `easy`, `medium`, `hard` | Yes | Subjective difficulty |
| source | string | origin ID | Optional | Where data came from (e.g. farmer, form submission) |
| notes | string | explanatory notes | Optional | Why this example is important |

### Intent Categories
```
livelihood_recommendation   - User asking for business/enterprise recommendation
scheme_search              - User asking for government schemes
training_request           - User asking for training/education
market_search              - User asking about markets/buyers/pricing
expert_request             - User asking to speak with expert
community                  - User asking about community/networking
general_question           - Ambiguous or general agriculture question
other                      - Doesn't fit above categories
```

### Size & Distribution Requirements

**Minimum Dataset**: 150 examples
**Recommended**: 300-500 examples
**Target Distribution**:

```
livelihood_recommendation:  60% (180-300 examples) - Most important
training_request:          15% (45-75 examples) - Currently weak
market_search:              10% (30-50 examples) - Moderate performance
scheme_search:               5% (15-25 examples) - Already works well
expert_request:              5% (15-25 examples) - Already works well
general_question:            3% (10-15 examples) - Uncommon but important
community:                   2% (5-10 examples) - Rare
```

**Language Distribution**:
```
Marathi:  50% (150-250 examples)
Hindi:    35% (105-175 examples)
English:  15% (45-75 examples)
```

**Difficulty Distribution**:
```
Easy:     25% (37-125 examples)
Medium:   50% (75-250 examples)
Hard:     25% (37-125 examples)
```

### Quality Guidelines

1. **Authenticity**: Must be real or realistic farmer queries
2. **Diversity**: Include multiple phrasing for same intent
3. **Context**: Include multi-entity, complex queries (not just simple ones)
4. **Coverage**: 
   - Different locations (Marathi regions, Hindi regions, etc)
   - Different demographics (age, experience levels)
   - Different enterprise types (crops, dairy, poultry, etc)
   - Different constraints (budget, land, water)

### Collection Strategy (When Ready)

1. **Phase 1**: Use existing evaluation dataset (60 examples)
2. **Phase 2**: Collect from actual system logs (with user consent)
3. **Phase 3**: Targeted collection for weak categories (livelihood, training)
4. **Phase 4**: Expand to under-represented languages (Hindi, English)

### Example Entries

```json
{"id": "train_intent_001", "text": "मी 50000 रुपये आणि 2 एकर जमीन आहे. कोणत्या शेतीच्या व्यवसायात हाती घालू?", "language": "marathi", "intent": "livelihood_recommendation", "difficulty": "medium", "source": "evaluation_dataset"}

{"id": "train_intent_002", "text": "मला शेतीच्या प्रशिक्षण कसे मिळेल?", "language": "marathi", "intent": "training_request", "difficulty": "easy", "source": "evaluation_dataset"}

{"id": "train_intent_003", "text": "सरकारी योजना कोणती आहेत?", "language": "marathi", "intent": "scheme_search", "difficulty": "easy", "source": "evaluation_dataset"}

{"id": "train_intent_004", "text": "मेरे पास 30000 रुपये हैं। क्या मैं खेती शुरू कर सकता हूं?", "language": "hindi", "intent": "livelihood_recommendation", "difficulty": "easy", "source": "evaluation_dataset"}

{"id": "train_intent_005", "text": "I have 1 acre and 50k rupees. What business should I start?", "language": "english", "intent": "livelihood_recommendation", "difficulty": "medium", "source": "evaluation_dataset"}

{"id": "train_intent_006", "text": "मी गेल्या 5 वर्षे शेती करत आहे आणि माझ्याकडे 3 एकर जमीन आहे. कोणता नवीन शेती मी सुरू करू शकते? बजेट 100000. पाणी उपलब्ध आहे.", "language": "marathi", "intent": "livelihood_recommendation", "difficulty": "hard", "source": "evaluation_dataset"}
```

---

## 2. Entity Extraction Training Data

### Purpose
Train ML model to extract and normalize entities from farmer queries.

### Format: JSONL with Entity Annotations

```json
{
  "id": "train_entity_001",
  "text": "मी 50000 रुपये आणि 2 एकर जमीन आहे.",
  "language": "marathi",
  "entities": [
    {
      "type": "budget_rupees",
      "value": 50000,
      "text_span": "50000 रुपये",
      "start_char": 2,
      "end_char": 17
    },
    {
      "type": "land_size_hectares",
      "value": 0.81,
      "text_span": "2 एकर",
      "start_char": 22,
      "end_char": 29,
      "note": "2 acres converted to 0.81 hectares"
    }
  ]
}
```

### Required Fields

| Field | Type | Values | Required | Notes |
|-------|------|--------|----------|-------|
| id | string | unique identifier | Yes | Format: `train_entity_<number>` |
| text | string | farmer query | Yes | Full sentence or phrase |
| language | string | `marathi`, `hindi`, `english` | Yes | Language of text |
| entities | array | Entity objects | Yes | See entity format below |

### Entity Object Format

| Field | Type | Values | Required | Notes |
|-------|------|--------|----------|-------|
| type | string | See entity types | Yes | What entity is this? |
| value | number/string | Normalized value | Yes | Standardized/parsed value |
| text_span | string | Original text | Yes | Exact text from input |
| start_char | number | Character position | Yes | 0-indexed start |
| end_char | number | Character position | Yes | 0-indexed end (exclusive) |
| note | string | Explanation | Optional | Why this value? (e.g. conversions) |

### Entity Types

```
budget_rupees              - Budget in Indian rupees (number)
land_size_hectares         - Land area in hectares (float, normalized)
location                   - Geographic location (string, normalized)
enterprise                 - Type of enterprise/business (string, normalized)
water_availability         - Water access level (enum: low/medium/high)
experience_level           - Farmer experience (enum: beginner/intermediate/expert)
time_availability          - Time commitment (enum: part_time/full_time)
willingness_to_learn       - Learning openness (boolean: true/false)
risk_tolerance             - Risk acceptance (enum: low/medium/high)
```

### Normalized Value Specifications

#### budget_rupees
- Type: Integer
- Range: 0 - 1000000+
- Format: Thousands converted to single number
- Examples:
  - "50000 रुपये" → 50000
  - "5 लाख रुपये" → 500000
  - "50 हजार" → 50000

#### land_size_hectares
- Type: Float (2 decimal places)
- Range: 0.1 - 100+
- Conversions:
  - 1 acre = 0.4047 hectares
  - 1 hectare = 2.471 acres
  - 1 bigha (varies by region) ≈ 0.67 hectares (Marathi regions)
- Examples:
  - "2 एकर" → 0.81
  - "1 हेक्टर" → 1.0
  - "50 गुंठे" → 1.34 (50 gunthe ≈ 0.5 hectares in Marathi)

#### location
- Type: String (normalized place name)
- Format: Lowercase, standardized spelling
- Include: State abbreviation if needed
- Examples:
  - "नाशिक" → "nashik_maharashtra"
  - "पुणे" → "pune_maharashtra"
  - "हरियाणा" → "haryana" (state-level)

#### enterprise
- Type: String (normalized enterprise name)
- Format: Lowercase, standardized
- Examples:
  - "मशरूम" → "mushroom_farming"
  - "मधुमाखी पालन" → "beekeeping"
  - "दुग्ध पशु" → "dairy_farming"

#### water_availability
- Type: Enum
- Values: `low`, `medium`, `high`
- Examples:
  - "पाणी कम आहे" → "low"
  - "पाणी उपलब्ध आहे" → "high"

#### experience_level
- Type: Enum
- Values: `beginner`, `intermediate`, `expert`
- Examples:
  - "नए किसान" → "beginner"
  - "5 साल का अनुभव" → "intermediate"
  - "20 वर्षों का अनुभव" → "expert"

#### time_availability
- Type: Enum
- Values: `part_time`, `full_time`
- Examples:
  - "पूरा समय काम कर सकते" → "full_time"
  - "सप्ताहांत में" → "part_time"

#### willingness_to_learn
- Type: Boolean
- Values: `true` (willing), `false` (not mentioned/unwilling)

#### risk_tolerance
- Type: Enum
- Values: `low`, `medium`, `high`

### Size & Distribution Requirements

**Minimum Dataset**: 200 examples
**Recommended**: 300-500 examples

**Entity Distribution** (% of examples containing entity):
```
enterprise:             60% (180-300 examples)
budget_rupees:          50% (150-250 examples)
land_size_hectares:     40% (120-200 examples)
location:               25% (75-125 examples)
water_availability:     20% (60-100 examples)
experience_level:       20% (60-100 examples)
time_availability:      15% (45-75 examples)
risk_tolerance:         15% (45-75 examples)
willingness_to_learn:   10% (30-50 examples)
```

**Language Distribution**:
```
Marathi:  50% (100-250 examples)
Hindi:    35% (70-175 examples)
English:  15% (30-75 examples)
```

### Quality Guidelines

1. **Accuracy**: Normalized values must be verified correct
2. **Completeness**: Mark all entities in each sentence
3. **Consistency**: Same value always normalized same way
4. **Span Accuracy**: Character positions must be exact
5. **Regional Variations**: Include different units/currencies by region

### Example Entries

```json
{"id": "train_entity_001", "text": "मी 50000 रुपये आणि 2 एकर जमीन आहे.", "language": "marathi", "entities": [{"type": "budget_rupees", "value": 50000, "text_span": "50000 रुपये", "start_char": 2, "end_char": 17}, {"type": "land_size_hectares", "value": 0.81, "text_span": "2 एकर", "start_char": 22, "end_char": 29}]}

{"id": "train_entity_002", "text": "नाशिकमध्ये मशरूम शेती करायची आहे.", "language": "marathi", "entities": [{"type": "location", "value": "nashik_maharashtra", "text_span": "नाशिकमध्ये", "start_char": 0, "end_char": 10}, {"type": "enterprise", "value": "mushroom_farming", "text_span": "मशरूम शेती", "start_char": 11, "end_char": 23}]}

{"id": "train_entity_003", "text": "मेरे पास 100000 रुपये हैं और 3 एकड़ जमीन है।", "language": "hindi", "entities": [{"type": "budget_rupees", "value": 100000, "text_span": "100000 रुपये", "start_char": 7, "end_char": 20}, {"type": "land_size_hectares", "value": 1.21, "text_span": "3 एकड़", "start_char": 26, "end_char": 33}]}
```

---

## 3. Other Potential Training Data

### Language-Specific Patterns (Not ML, but needed reference)
Location: `data/training/language_specific_entities.json`

```json
{
  "marathi": {
    "enterprises": {
      "मशरूम": "mushroom_farming",
      "मधु": "beekeeping",
      "भेडी": "sheep_farming"
    },
    "locations": {
      "नाशिक": "nashik_maharashtra",
      "पुणे": "pune_maharashtra"
    }
  },
  "hindi": {
    "enterprises": {
      "मशरूम": "mushroom_farming",
      "मधु पालन": "beekeeping"
    }
  }
}
```

---

## 4. Collection & Storage Strategy

### Storage Format
- **Location**: `data/training/`
- **File Format**: JSONL (one JSON object per line)
- **Naming**: 
  - Intent: `intent_training_<version>.jsonl`
  - Entities: `entity_training_<version>.jsonl`
- **Versioning**: `v1`, `v2`, etc as data grows

### Collection Phases

**Phase 1: Initial (Week 1-2)**
- Use existing evaluation dataset (60 examples)
- Manually annotate 50-100 additional examples from system logs
- Target: 150 intent examples, 100 entity examples

**Phase 2: Expansion (Week 2-4)**
- Collect from real system interactions (farmer queries)
- Annotate additional 200-300 examples
- Target: 300+ intent examples, 200+ entity examples

**Phase 3: Refinement (Week 4+)**
- Targeted collection for weak categories
- Expand language coverage
- Validate annotation quality (inter-annotator agreement)

### Quality Assurance

1. **Annotation Guidelines**
   - Create detailed guidelines document before collection
   - Include examples for each entity type
   - Define how to handle ambiguous cases

2. **Inter-Annotator Agreement**
   - Have 2+ people annotate 20-30 examples
   - Calculate Cohen's Kappa
   - Target: >0.85 agreement

3. **Validation**
   - Check for consistency (same intent always labeled same way)
   - Verify entity value conversions (budget, land, etc)
   - Spot-check character spans

---

## 5. Validation Strategy

### Train/Test Split
```
Training Set: 70% - Used to train model
Validation Set: 15% - Used for hyperparameter tuning
Test Set: 15% - Used for final evaluation (never seen during training)
```

### Cross-Validation
- Use 5-fold cross-validation for smaller datasets (<500 examples)
- Stratified by intent/language to maintain distribution

### Language-Specific Evaluation
- Evaluate model performance separately for each language
- Ensure no regression on any single language

---

## 6. Key Constraints

### ⚠️ DO NOT
- ❌ Create synthetic/fake examples
- ❌ Use machine translation (not authentic)
- ❌ Over-represent any single region/user
- ❌ Include examples without proper consent
- ❌ Combine examples into mixed language without real justification

### ✓ DO
- ✓ Use real or realistic farmer queries
- ✓ Maintain original language (no translation)
- ✓ Get user consent for data usage
- ✓ Document data source and collection method
- ✓ Include diverse farmers, regions, enterprises

---

## 7. Timeline & Effort Estimate

| Phase | Timeline | Effort | Output |
|-------|----------|--------|--------|
| Specification (this doc) | Week 1 | Low | This document |
| Phase 1 Collection | Week 1-2 | Medium | 150 intent + 100 entity examples |
| Phase 2 Collection | Week 2-4 | High | +200 intent + 200 entity examples |
| ML Model Training | Week 3-4 | High | Trained model + evaluation report |
| Validation & Testing | Week 4-5 | Medium | Final metrics, deployment decision |

**Total Effort**: 2-3 weeks if ML decision made
**Resource Required**: 1-2 people (annotation), 1 ML engineer (training)

---

## 8. Next Steps (When ML is Approved)

1. Create detailed **Annotation Guidelines** (template provided separately)
2. Set up **Data Collection Infrastructure** (forms, APIs, logging)
3. Start **Phase 1 Collection** (first 50-100 examples)
4. Begin **Quality Assurance Process** (inter-annotator agreement)
5. Prepare **Model Training Environment** (Jupyter, GPU setup)

---

## Appendix: Example Annotation Template

```markdown
# Entity Annotation Template

**Query**: "मी नाशिकमध्ये 2 एकर जमीन आहे आणि 50000 रुपये बजेट आहे. मशरूम शेती सुरू करू शकते का?"

**Annotator**: [Name]
**Date**: 2026-08-19
**Language**: Marathi
**Difficulty**: Medium

## Entities Found

| Type | Text Span | Normalized Value | Start | End | Confidence |
|------|-----------|------------------|-------|-----|-----------|
| location | नाशिकमध्ये | nashik_maharashtra | 2 | 12 | High |
| land_size_hectares | 2 एकर | 0.81 | 14 | 20 | High |
| budget_rupees | 50000 रुपये | 50000 | 26 | 37 | High |
| enterprise | मशरूम शेती | mushroom_farming | 44 | 57 | High |

## Notes
- Clear, straightforward entities
- All values straightforward to normalize
- Good example for training
```

