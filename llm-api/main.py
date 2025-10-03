from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from config import settings
from routes import router
from db import mongo_client

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
    logger.info("Starting LLM Chat API with GitHub Models...")
    try:
        await mongo_client.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down LLM Chat API...")
    await mongo_client.close()

# Create FastAPI app
app = FastAPI(
    title="LLM Chat API",
    description="Chat microservice with GitHub Models and MongoDB storage",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "llm-chat-api",
        "version": "1.0.0",
        "provider": "GitHub Models"
    }

# Root endpoint


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "LLM Chat API",
        "version": "1.0.0",
        "description": "Chat with GitHub Models (GPT-4, Llama, Mistral, etc.)",
        "provider": "GitHub Models",
        "endpoints": {
            "health": "/health",
            "create_session": "POST /chat/session",
            "send_message": "POST /chat/message",
            "get_session": "GET /chat/session/{session_id}",
            "list_sessions": "GET /chat/sessions",
            "list_models": "GET /chat/models"
        }
    }

# Global exception handler


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.NODE_ENV == "development"
    )
