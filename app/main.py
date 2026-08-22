"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.routes import (
    health_router,
    intent_router,
    advisory_router,
    assistant_router,
)

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Multilingual AI platform for farmer livelihoods",
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route routers
app.include_router(health_router)
app.include_router(intent_router)
app.include_router(advisory_router)
app.include_router(assistant_router)

# Log available routes at startup
logger.info(f"KrishiMitra {settings.app_name} initialized")
logger.info(f"Environment: {settings.app_env}")
logger.info(f"Debug mode: {settings.debug}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
