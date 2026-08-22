# KrishiMitra API — Quick Start Guide

## Installation & Startup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload

# Server running at: http://localhost:8000
```

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Health Check:** http://localhost:8000/health

---

## Core Endpoints

### 1. Intent Detection

Detect what the farmer is asking for.

**Endpoint:** `POST /api/v1/intent/detect`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/intent/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "मशरूम शेती कशी सुरू करू?",
    "language": "marathi"
  }'
```

**Intents:**
- `livelihood_recommendation` - "What business can I start?"
- `scheme_search` - "What government schemes are available?"
- `training_request` - "How do I learn about beekeeping?"
- `market_search` - "Where can I sell my product?"
- `expert_request` - "I need expert guidance"
- `community` - "Community discussions"
- `general_question` - Other questions

---

### 2. Get Recommendations

Get personalized business recommendations.

**Endpoint:** `POST /api/v1/advisory/recommend`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/advisory/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "budget_rupees": 50000,
    "land_size_hectares": 2.0,
    "state": "maharashtra",
    "experience_level": "beginner"
  }'
```

**Returns:**
- Top 3 recommended enterprises
- Suitability scores
- Investment requirements
- Training recommendations
- Relevant schemes
- Market opportunities
- Risks and requirements

---

### 3. Main Assistant Chat

The main entry point that handles everything.

**Endpoint:** `POST /api/v1/assistant/chat`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/assistant/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have 50000 rupees. What can I start?",
    "language": "english",
    "farmer_context": {
      "budget": 50000,
      "land": 2.0,
      "experience": "beginner"
    }
  }'
```

**What it does:**
1. Detects language
2. Identifies intent
3. Routes to appropriate service
4. Returns personalized response

---

## Language Support

All endpoints support:
- `english` - English text
- `hindi` - हिंदी
- `marathi` - मराठी
- `auto` - Auto-detect (if not sure)

**Example with auto-detection:**
```json
{
  "message": "मला शेळीपालन सुरू करायचे",
  "language": "auto"
}
```

---

## Sample Data

### Enterprises Available
- Apiculture (Beekeeping)
- Poultry Farming
- Fisheries
- Goat Farming
- Mushroom Cultivation
- Vermicomposting

### States
- Maharashtra (primary - "maharashtra")
- Others supported through schemes data

### Languages
- Marathi (primary)
- Hindi (secondary)
- English (fallback)

---

## Error Handling

All endpoints return proper HTTP status codes and error messages:

```json
{
  "detail": {
    "error": "Message cannot be empty",
    "error_code": "empty_message",
    "details": {
      "field": "message"
    }
  }
}
```

**Common Error Codes:**
- `invalid_request` - Malformed request
- `invalid_budget` - Budget validation failed
- `invalid_language` - Unsupported language
- `empty_message` - No message provided
- `service_error` - Server-side error
- `not_implemented` - Feature coming soon

---

## Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# API tests only
pytest tests/test_api_integration.py -v

# Existing unit tests
pytest tests/test_advisory_engine.py tests/test_intent_router.py -v

# With coverage
pytest tests/ --cov=app
```

---

## Example Workflows

### Workflow 1: Basic Livelihood Planning
```bash
# 1. Ask for recommendations
curl -X POST "http://localhost:8000/api/v1/assistant/chat" \
  -d '{"message": "I have 50000 rupees. What can I do?", "language": "english"}'

# 2. Get details on recommended enterprise
curl -X GET "http://localhost:8000/api/v1/advisory/enterprises/apiculture"

# 3. Find relevant schemes
curl -X GET "http://localhost:8000/api/v1/advisory/schemes/apiculture?state=maharashtra"
```

### Workflow 2: Market Research
```bash
# 1. Detect that user wants market info
curl -X POST "http://localhost:8000/api/v1/intent/detect" \
  -d '{"message": "Where can I sell honey?", "language": "english"}'

# 2. Get market data via assistant
curl -X POST "http://localhost:8000/api/v1/assistant/chat" \
  -d '{"message": "Where can I sell honey?", "language": "english"}'
```

### Workflow 3: Training Request
```bash
# 1. Ask about training
curl -X POST "http://localhost:8000/api/v1/assistant/chat" \
  -d '{"message": "How do I start mushroom cultivation?", "language": "english"}'

# Response includes training modules and expert contact options
```

---

## Request/Response Format

### All requests use JSON:
```json
{
  "message": "Your question here",
  "language": "english",
  "farmer_context": {
    "budget": 50000,
    "land": 2.0,
    "experience": "beginner"
  }
}
```

### All responses use JSON:
```json
{
  "intent": "livelihood_recommendation",
  "response": "Response text here...",
  "response_type": "advisory",
  "requires_further_input": false,
  "suggested_next_action": "Next step...",
  "metadata": {}
}
```

---

## Data Notes

⚠️ **Important:** This is MVP/prototype data
- Enterprise recommendations are based on simple scoring
- Scheme information is prototype (verify official sources)
- Market prices are indicative only
- All data is marked with `"is_prototype_data": true` where applicable

---

## Architecture

```
Request
  ↓
Language Detection
  ↓
Intent Router
  ↓
Service Layer (Advisory, Scheme, Training, Market, Expert)
  ↓
Data Provider (JSON fixtures)
  ↓
Response
```

Each layer is independent and can be replaced:
- Language detection → Use Google Translate API later
- Intent router → Use NLP model later
- Data provider → Use PostgreSQL later
- Services → Add real AI integration later

---

## Performance Notes

- First request loads JSON fixtures into memory (100ms)
- Subsequent requests served from cache (~10ms)
- No external API calls required for core features
- Advisory scoring is deterministic (no LLM overhead)

---

## Next Steps

1. **Farmer Context** - Add persistent farmer profiles
2. **Voice Support** - Integrate speech-to-text
3. **Database** - Replace JSON with PostgreSQL
4. **Advanced AI** - Add LLM for complex queries
5. **RAG** - Add knowledge base search

---

## Support

For issues or questions:
- Check `/docs` for interactive API documentation
- Review test cases in `tests/test_api_integration.py`
- Check TASK_1_REPORT.md for detailed documentation
- All code is well-commented

---

**Version:** 0.1.0  
**Last Updated:** August 19, 2026  
**Status:** Ready for Testing
