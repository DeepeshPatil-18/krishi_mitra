# KrishiMitra Backend

A multilingual, voice-enabled AI livelihood platform for farmers.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+

### Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize database:
   ```bash
   python -m alembic upgrade head
   ```

6. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Architecture

### Core Modules

- **api/** - FastAPI route handlers
- **services/** - Business logic and orchestration
- **models/** - SQLAlchemy ORM models
- **schemas/** - Pydantic request/response schemas
- **core/** - Configuration, constants, utilities
- **data/** - Static data (schemes, enterprises, etc.)
- **tests/** - Test suite

### Data Flow

```
Farmer → Text/Voice → Language Layer → Intent Router
    ↓
AI Orchestrator
    ↓
[Advisory Engine | Scheme Service | Training | Market | Expert]
    ↓
Response Generation → Text/TTS → Farmer
```

## Key Features

1. **Livelihood Recommendation** - Enterprise suggestion based on farmer context
2. **Government Scheme Matching** - Find relevant subsidies and schemes
3. **Agricultural Training** - Structured learning paths per enterprise
4. **Market Linkage** - Connect farmers with buyers
5. **Expert Assistance** - Request expert support with ticketing
6. **Multilingual Support** - Marathi, Hindi, English
7. **Voice Integration** - Speech-to-text and text-to-speech

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Database Migrations
```bash
alembic init alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Environment Variables

See `.env.example` for all configuration options.

For the hackathon prototype, a demo farmer context is provided to skip authentication.
