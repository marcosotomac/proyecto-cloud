from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageGenerationRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    seed: Optional[int] = None
    style: Optional[str] = None
    model: Optional[str] = "flux"


class ImageGenerationResponse(BaseModel):
    id: str
    status: str = "completed"
    prompt: str
    user_id: Optional[str] = None
    s3: dict
    meta: dict


class S3Artifacts(BaseModel):
    record: str
    image: str
    preview: Optional[str] = None


class ImageRecord(BaseModel):
    id: str
    userId: Optional[str] = None
    username: Optional[str] = None
    service: str = "image"
    provider: str = "pollinations"
    model: str
    prompt: str
    promptHash: str
    status: int
    latencyMs: int
    tokens: dict = {"in": 0, "out": 0}
    size: dict
    cost: dict = {"usd": 0.0}
    createdAt: str
    artifacts: dict
    meta: dict
