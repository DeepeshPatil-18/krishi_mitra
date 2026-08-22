"""Health check endpoints"""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": "0.1.0"
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to KrishiMitra",
        "version": "0.1.0",
        "status": "operational",
        "documentation": "/docs",
        "openapi": "/openapi.json"
    }
