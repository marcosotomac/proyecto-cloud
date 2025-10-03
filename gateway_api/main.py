from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import sys
import httpx
from datetime import datetime

from config import settings
from service_client import (
    users_client,
    llm_client,
    image_client,
    speech_client,
    analytics_client
)

# Import routers
from routes_auth import router as auth_router
from routes_chat import router as chat_router
from routes_image import router as image_router
from routes_speech import router as speech_router
from routes_analytics import router as analytics_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting API Gateway...")
    logger.info(f"Environment: {settings.NODE_ENV}")
    logger.info(f"Port: {settings.PORT}")
    logger.info(f"Analytics Enabled: {settings.ENABLE_ANALYTICS}")

    # Check service health
    await check_services_health()

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")


async def check_services_health():
    """Check health of all microservices"""
    services = {
        "Users": (users_client, "/"),
        "LLM Chat": (llm_client, "/health"),
        "Image": (image_client, "/healthz"),
        "Speech": (speech_client, "/healthz"),
        "Analytics": (analytics_client, "/health")
    }

    for name, (client, endpoint) in services.items():
        try:
            response = await client.request("GET", endpoint)
            if response.status_code == 200:
                logger.info(f"✓ {name} service is healthy")
            else:
                logger.warning(
                    f"⚠ {name} service returned {response.status_code}")
        except Exception as e:
            logger.error(f"✗ {name} service unavailable: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="LLM Platform API Gateway",
    description="Unified API Gateway for LLM microservices platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(image_router)
app.include_router(speech_router)
app.include_router(analytics_router)

# Root endpoint


@app.get("/")
async def root():
    """Gateway information"""
    return {
        "gateway": "LLM Platform API Gateway",
        "version": "1.0.0",
        "description": "Unified API Gateway for LLM microservices platform",
        "services": {
            "users": settings.USERS_SERVICE_URL,
            "llm_chat": settings.LLM_SERVICE_URL,
            "text_to_image": settings.IMAGE_SERVICE_URL,
            "text_to_speech": settings.SPEECH_SERVICE_URL,
            "analytics": settings.ANALYTICS_SERVICE_URL
        },
        "endpoints": {
            "authentication": [
                "POST /api/auth/register",
                "POST /api/auth/login",
                "POST /api/auth/refresh",
                "GET /api/auth/profile"
            ],
            "llm_chat": [
                "POST /api/chat",
                "GET /api/chat/sessions",
                "GET /api/chat/sessions/{session_id}",
                "GET /api/chat/models"
            ],
            "text_to_image": [
                "POST /api/image/generate",
                "GET /api/image/models"
            ],
            "text_to_speech": [
                "POST /api/speech/generate",
                "GET /api/speech/voices"
            ],
            "analytics": [
                "GET /api/analytics/user/me",
                "GET /api/analytics/service/{service_type}",
                "GET /api/analytics/system",
                "GET /api/analytics/usage"
            ]
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

# Health check endpoint


@app.get("/health")
async def health_check():
    """Gateway health check"""
    services_status = {}

    # Check all services
    services = {
        "users": (users_client, "/"),
        "llm_chat": (llm_client, "/health"),
        "image": (image_client, "/healthz"),
        "speech": (speech_client, "/healthz"),
        "analytics": (analytics_client, "/health")
    }

    all_healthy = True

    for name, (client, endpoint) in services.items():
        try:
            response = await client.request("GET", endpoint)
            is_healthy = response.status_code == 200
            services_status[name] = "healthy" if is_healthy else "unhealthy"
            if not is_healthy:
                all_healthy = False
        except Exception as e:
            services_status[name] = "unavailable"
            all_healthy = False

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.NODE_ENV == "development"
    )
