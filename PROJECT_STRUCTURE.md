# KrishiMitra Project Structure

A hackathon MVP for agricultural advisory chatbot supporting Marathi, Hindi, and English farmer queries.

---

## Directory Overview

```
krishimitra_backend/
├── app/                          # Application source code (production)
│   ├── api/                      # REST API endpoints
│   │   ├── routes/               # Route handlers (advisory, assistant, health, etc.)
│   │   └── responses.py          # API response models
│   ├── core/                     # Core configuration
│   │   ├── config.py             # App configuration
│   │   └── constants.py          # Global constants
│   ├── data/                     # Static data files (JSON)
│   │   ├── enterprises.json      # Agricultural enterprises reference
│   │   ├── experts.json          # Expert profiles
│   │   ├── markets.json          # Market information
│   │   ├── schemes.json          # Government schemes
│   │   └── training_modules.json # Training resources
│   ├── models/                   # Data models (Pydantic)
│   │   ├── base.py               # Base models
│   │   ├── community.py          # Community entity
│   │   ├── enterprise.py         # Enterprise entity
│   │   ├── expert.py             # Expert entity
│   │   ├── farmer.py             # Farmer context entity
│   │   ├── market.py             # Market entity
│   │   ├── scheme.py             # Scheme entity
│   │   └── training.py           # Training entity
│   ├── schemas/                  # Request/response schemas
│   │   ├── advisory.py           # Advisory request/response
│   │   ├── expert.py             # Expert request/response
│   │   ├── farmer.py             # Farmer context schema
│   │   ├── intent.py             # Intent schema
│   │   ├── market.py             # Market schema
│   │   └── scheme.py             # Scheme schema
│   ├── services/                 # Business logic layer
│   │   ├── advisory_engine.py    # Advisory recommendations engine
│   │   ├── ai_orchestrator.py    # Main orchestrator (routes all requests)
│   │   ├── ai_service.py         # AI utilities
│   │   ├── data_provider.py      # Data access layer
│   │   ├── entity_extractor.py   # Entity extraction (deterministic)
│   │   ├── entity_normalizer.py  # Entity normalization
│   │   ├── intent_router.py      # Intent classification
│   │   ├── language_service.py   # Language detection
│   │   ├── response_grounder.py  # Response grounding
│   │   ├── scoring_system.py     # Enterprise matching/scoring
│   │   └── voice_service.py      # Voice handling (placeholder)
│   └── main.py                   # FastAPI app initialization
│
├── tests/                        # Test suite
│   ├── test_entity_extractor_task45.py      # Entity extraction tests (82 tests)
│   ├── test_entity_pipeline_integration.py  # Integration tests (18 tests)
│   ├── test_advisory_engine.py              # Advisory engine tests
│   ├── test_advisory_engine_v2.py           # Advisory engine v2 tests
│   ├── test_api_integration.py              # API integration tests
│   ├── test_intent_router.py                # Intent routing tests
│   ├── test_orchestrator_simple.py          # Orchestrator basic tests
│   └── test_orchestrator_task3.py           # Orchestrator advanced tests
│
├── scripts/                      # Analysis and utility scripts (non-production)
│   ├── analyze_errors.py         # Error analysis utility
│   ├── analyze_errors_simple.py  # Simplified error analysis
│   ├── evaluate_farmer_dataset.py # Evaluation runner
│   ├── task_4_2_evaluation.py    # TASK 4.2 specific evaluation
│   ├── test_entity_normalization_baseline.py
│   └── test_entity_normalizer.py
│
├── data/                         # Data and evaluation results
│   ├── evaluation/               # Evaluation datasets and results
│   │   ├── farmer_queries.jsonl  # 60-query farmer dataset (production eval)
│   │   ├── task_4_5_results.json # TASK 4.5 final evaluation results
│   │   │                         # (Entity 78.7%, Intent 61.7%, Language 100%)
│   │   └── [other eval results]  # Historical evaluation outputs
│   └── [other data files]
│
├── docs/                         # Documentation
│   ├── archive/
│   │   └── task-4/               # Historical TASK 4 reports and outputs
│   │       ├── TASK_4_1_*.md/txt # TASK 4.1 reports
│   │       ├── TASK_4_2_*.md/txt # TASK 4.2 reports
│   │       ├── TASK_4_3_*.md/txt # TASK 4.3 reports
│   │       ├── TASK_4_4_*.md/txt # TASK 4.4 reports
│   │       └── [temporary files, debug outputs]
│   └── [future documentation]
│
├── TASK_1_REPORT.md              # TASK 1 completion report (API foundation)
├── TASK_2_REPORT.md              # TASK 2 completion report (Advisory engine v2)
├── TASK_3_REPORT.md              # TASK 3 completion report (AI Orchestrator)
├── TASK_4_5_FINAL_REPORT.md      # TASK 4.5 final report
│                                 # (Entity enhancement: 51.1% → 78.7%)
├── TASK_4_6_FINAL_DECISION.md    # TASK 4.6 final decision (GO for hackathon)
│
├── API_QUICK_START.md            # Quick start guide for API
├── README.md                     # Project overview
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── run_evaluation.py             # Main evaluation script
└── .env.example                  # Environment variables template
```

---

## Key Metrics (Current Status)

| Component | Metric | Status |
|-----------|--------|--------|
| **Entity Extraction** | 78.7% accuracy | ✅ Strong |
| **Intent Detection** | 61.7% accuracy | ⚠️ Acceptable |
| **Language Detection** | 100.0% accuracy | ✅ Excellent |
| **Tests** | 100/100 passing | ✅ Zero failures |
| **False Positives** | 1 (down from 18) | ✅ Excellent |
| **Regressions** | 0 | ✅ None |

---

## Important Files

### Active Source Code (DO NOT MODIFY LIGHTLY)
- `app/services/entity_extractor.py` — Deterministic entity extraction (HIGH QUALITY, 78.7%)
- `app/services/intent_router.py` — Intent classification
- `app/services/language_service.py` — Language detection
- `app/services/ai_orchestrator.py` — Main orchestration logic

### Active Test Suite (VERIFY AFTER ANY CHANGES)
- `tests/test_entity_extractor_task45.py` — 82 unit tests
- `tests/test_entity_pipeline_integration.py` — 18 integration tests
- Run all: `pytest tests/ -v`

### Production Evaluation Data
- `data/evaluation/farmer_queries.jsonl` — 60-query dataset (TASK 4.4 baseline, used in all subsequent tasks)
- `data/evaluation/task_4_5_results.json` — Latest production evaluation results

### Current Status Documents
- `TASK_4_5_FINAL_REPORT.md` — Latest entity extraction report (detailed, 20 sections)
- `TASK_4_6_FINAL_DECISION.md` — Latest system decision (GO for hackathon MVP)

### Historical Archive
- `docs/archive/task-4/` — All TASK 4 intermediate reports, debug outputs, and temporary files
- Not needed for current development; archived for reference

---

## Quick Reference

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_entity_extractor_task45.py -v

# Integration only
pytest tests/test_entity_pipeline_integration.py -v
```

### Running Evaluation
```bash
# Full evaluation on 60-query dataset
python run_evaluation.py

# Results saved to data/evaluation/task_4_5_results.json
```

### Running API
```bash
# See API_QUICK_START.md for details
python -m uvicorn app.main:app --reload
```

---

## Project Status

**Current Phase**: TASK 4 Complete — Text pipeline validation passed

**System Ready**: ✅ YES for hackathon MVP
- Entity extraction: 78.7% (strong)
- Intent routing: 61.7% (acceptable)
- Language: 100% (excellent)
- All core capabilities working end-to-end

**Next Phase**: TASK 5 — Scheme Search Capability (build product features, not optimize text further)

---

## Notes

- The project uses **deterministic (regex-based) entity extraction**, not ML. This is intentional and proven effective (78.7% accuracy).
- **No external AI APIs are used** for core processing; all logic is self-contained.
- **Language support**: Marathi, Hindi, English (all working, multilingual patterns implemented)
- **Hackathon focus**: Demonstration of working solution, not theoretical 100% accuracy
- All changes since TASK 4.5 are documented in TASK_4_6_FINAL_DECISION.md

---

**Last updated**: August 22, 2026  
**Status**: Production-ready for hackathon MVP
