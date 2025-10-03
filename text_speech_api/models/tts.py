"""Pydantic models for Text-to-Speech API"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class TTSGenerateRequest(BaseModel):
    """Request model for TTS generation"""
    prompt: str = Field(..., description="Text to synthesize",
                        min_length=1, max_length=5000)
    model: str = Field(
        default="gtts", description="TTS model to use (gtts, gtts-slow)")
    voice: str = Field(
        default="en", description="Language code (en, es, fr, de, it, pt, ja, zh-CN, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Hello, this is a test of text to speech synthesis",
                "model": "gtts",
                "voice": "en"
            }
        }


class S3Keys(BaseModel):
    """S3 object keys for TTS artifacts"""
    record: str = Field(..., description="Path to record.json metadata")
    audio: str = Field(..., description="Path to audio output file")
    input: Optional[str] = Field(
        None, description="Path to input.json parameters")


class TTSMetadata(BaseModel):
    """Metadata about the TTS generation"""
    provider: str = Field(..., description="TTS provider used")
    model: str = Field(..., description="Model used")
    voice: str = Field(..., description="Voice used")
    duration_seconds: Optional[float] = Field(
        None, description="Audio duration in seconds")
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds")


class TTSGenerateResponse(BaseModel):
    """Response model for TTS generation"""
    id: str = Field(..., description="Unique request ID")
    s3: S3Keys = Field(..., description="S3 paths to artifacts")
    meta: TTSMetadata = Field(..., description="Generation metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    user_id: Optional[str] = Field(
        None, description="User ID if authenticated")
    status: str = Field(default="completed", description="Generation status")


class TTSRecord(BaseModel):
    """Complete record stored in S3"""
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    service: str = "tts"
    provider: str
    model: str
    voice: str
    prompt: str
    status: int
    latency_ms: int
    cost: Dict[str, float] = Field(default_factory=lambda: {"usd": 0.0})
    artifacts: Dict[str, str]
    created_at: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class TTSInfoResponse(BaseModel):
    """Response for TTS info endpoint"""
    id: str
    prompt: str
    model: str
    voice: str
    status: str
    created_at: datetime
    user_id: Optional[str] = None
    s3_key: str


class TTSDownloadResponse(BaseModel):
    """Response for TTS download endpoint"""
    download_url: str = Field(..., description="Signed URL for audio download")
    expires_in: int = Field(..., description="URL expiration time in seconds")


class TTSListResponse(BaseModel):
    """Response for listing TTS generations"""
    audios: list[TTSInfoResponse]
    total: int
    page: int
    per_page: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
