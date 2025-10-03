from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============= User Service Models =============


class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: str
    password: str


class UserLoginRequest(BaseModel):
    """User login request"""
    email: str
    password: str


class UserAuthResponse(BaseModel):
    """User authentication response"""
    accessToken: str
    refreshToken: str
    user: Dict[str, Any]

# ============= LLM Chat Models =============


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model - simplified to match backend"""
    message: str
    model: Optional[str] = "gpt-4o-mini"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    session_id: str
    message_id: str
    content: str
    role: str
    model: str
    tokens: Dict[str, int]

# ============= Text-to-Image Models =============


class ImageGenerationRequest(BaseModel):
    """Image generation request"""
    prompt: str
    model: Optional[str] = None
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    nologo: Optional[bool] = True
    enhance: Optional[bool] = False


class ImageGenerationResponse(BaseModel):
    """Image generation response - matches backend"""
    id: str
    status: str
    prompt: str
    user_id: Optional[str] = None
    s3: Dict[str, str]  # Contains 'record' and 'image' keys
    # Contains 'provider', 'model', 'size', 'latencyMs', 'contentType'
    meta: Dict[str, Any]

# ============= Text-to-Speech Models =============


class SpeechGenerationRequest(BaseModel):
    """Speech generation request - matches backend"""
    prompt: str  # Text to convert to speech
    # Language code for gTTS (en, es, fr, de, etc.)
    voice: Optional[str] = "en"
    language: Optional[str] = "en"  # Deprecated, kept for compatibility
    model: Optional[str] = "gtts"  # gtts or gtts-slow


class SpeechGenerationResponse(BaseModel):
    """Speech generation response - matches backend"""
    id: str
    status: str
    user_id: Optional[str] = None
    s3: Dict[str, Optional[str]]  # Contains 'record', 'audio', 'input' keys
    # Contains 'provider', 'model', 'voice', 'processing_time_ms'
    meta: Dict[str, Any]
    created_at: datetime

# ============= Analytics Models =============


class AnalyticsEventRequest(BaseModel):
    """Analytics event tracking request"""
    service_type: str
    event_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserAnalyticsResponse(BaseModel):
    """User analytics response"""
    user_id: Optional[str]
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    llm_chat_requests: int
    image_generation_requests: int
    speech_generation_requests: int
    total_tokens: int = 0

# ============= Gateway Models =============


class HealthResponse(BaseModel):
    """Gateway health check response"""
    status: str = "healthy"
    service: str = "api-gateway"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)


class ServiceInfo(BaseModel):
    """Service information"""
    name: str
    url: str
    status: str
    version: Optional[str] = None


class GatewayInfoResponse(BaseModel):
    """Gateway information response"""
    gateway: str = "LLM Platform API Gateway"
    version: str = "1.0.0"
    description: str = "Unified API Gateway for LLM microservices platform"
    services: List[ServiceInfo]
    endpoints: Dict[str, List[str]]


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: Optional[str] = None
