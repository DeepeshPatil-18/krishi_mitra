"""API route modules"""

from app.api.routes.health import router as health_router
from app.api.routes.intent import router as intent_router
from app.api.routes.advisory import router as advisory_router
from app.api.routes.assistant import router as assistant_router

__all__ = [
    "health_router",
    "intent_router",
    "advisory_router",
    "assistant_router",
]
