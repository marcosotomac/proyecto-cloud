"""Text-to-Speech API - Main Application"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import settings
from routes.tts import router as tts_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🎤 Text-to-Speech API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"S3 Bucket: {settings.s3_bucket}")
    logger.info(f"TTS Provider: gTTS (Google Text-to-Speech)")

    # Initialize database
    try:
        from db import init_db
        init_db()
        logger.info("✅ PostgreSQL database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        # Don't fail startup if DB is not available

    yield
    logger.info("🛑 Text-to-Speech API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Text-to-Speech API",
    description="Text-to-Speech microservice using gTTS (Google Text-to-Speech)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "text-to-speech",
        "version": "1.0.0",
        "provider": "gtts"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "text-to-speech-api",
        "version": "1.0.0",
        "endpoints": {
            "health": "/healthz",
            "generate": "POST /tts/generate",
            "info": "GET /tts/{id}",
            "download": "GET /tts/{id}/download",
            "list": "GET /tts/admin/audios (auth required)"
        }
    }


# Include routers
app.include_router(tts_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
