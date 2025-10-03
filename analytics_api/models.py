from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ServiceType(str, Enum):
    """Types of services being tracked"""
    LLM_CHAT = "llm_chat"
    TEXT_TO_IMAGE = "text_to_image"
    TEXT_TO_SPEECH = "text_to_speech"


class EventType(str, Enum):
    """Types of analytics events"""
    REQUEST = "request"
    SUCCESS = "success"
    ERROR = "error"
    GENERATION = "generation"

# ============= Analytics Event Models =============


class AnalyticsEvent(BaseModel):
    """Base analytics event model"""
    event_id: str = Field(..., description="Unique event ID")
    user_id: Optional[str] = Field(
        None, description="User ID (null for anonymous)")
    service_type: ServiceType = Field(...,
                                      description="Service that generated the event")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional event metadata")


class LLMChatEvent(AnalyticsEvent):
    """LLM Chat specific analytics"""
    session_id: Optional[str] = None
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    response_time_ms: Optional[float] = None


class ImageGenerationEvent(AnalyticsEvent):
    """Image generation specific analytics"""
    image_id: Optional[str] = None
    prompt_length: Optional[int] = None
    image_size: Optional[str] = None
    generation_time_ms: Optional[float] = None
    s3_size_bytes: Optional[int] = None


class SpeechGenerationEvent(AnalyticsEvent):
    """Speech generation specific analytics"""
    audio_id: Optional[str] = None
    text_length: Optional[int] = None
    voice: Optional[str] = None
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    audio_size_bytes: Optional[int] = None

# ============= Analytics Request/Response Models =============


class TrackEventRequest(BaseModel):
    """Request to track an analytics event"""
    user_id: Optional[str] = None
    service_type: ServiceType
    event_type: EventType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TrackEventResponse(BaseModel):
    """Response after tracking an event"""
    event_id: str
    timestamp: datetime
    message: str = "Event tracked successfully"

# ============= Analytics Query Models =============


class TimeRange(str, Enum):
    """Time range for analytics queries"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


class UserAnalyticsResponse(BaseModel):
    """User-specific analytics response"""
    user_id: Optional[str]
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0

    # Service-specific counts
    llm_chat_requests: int = 0
    image_generation_requests: int = 0
    speech_generation_requests: int = 0

    # Token usage (LLM only)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Storage usage
    total_storage_bytes: int = 0

    # Time metrics
    avg_response_time_ms: Optional[float] = None
    first_request: Optional[datetime] = None
    last_request: Optional[datetime] = None


class ServiceAnalyticsResponse(BaseModel):
    """Service-specific analytics response"""
    service_type: ServiceType
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0
    unique_users: int = 0
    anonymous_users: int = 0
    avg_response_time_ms: Optional[float] = None

    # Service-specific metrics
    service_metrics: Dict[str, Any] = Field(default_factory=dict)


class SystemAnalyticsResponse(BaseModel):
    """System-wide analytics response"""
    total_requests: int = 0
    total_users: int = 0
    total_anonymous_requests: int = 0

    # Per-service breakdown
    services: List[ServiceAnalyticsResponse] = Field(default_factory=list)

    # Top users
    top_users: List[Dict[str, Any]] = Field(default_factory=list)

    # Time metrics
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UsageStatsResponse(BaseModel):
    """Detailed usage statistics"""
    time_range: str
    user_id: Optional[str] = None

    # Request counts by day/hour
    requests_by_period: Dict[str, int] = Field(default_factory=dict)

    # Request counts by service
    requests_by_service: Dict[str, int] = Field(default_factory=dict)

    # Success/failure rates
    success_rate_by_service: Dict[str, float] = Field(default_factory=dict)

    # Peak usage times
    peak_hour: Optional[int] = None
    peak_day: Optional[str] = None

# ============= Health Check Model =============


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "analytics-api"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: str = "connected"
