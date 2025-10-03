from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class TokenCount(BaseModel):
    input: int = 0
    output: int = 0


class SessionCounters(BaseModel):
    messages: int = 0
    tokensIn: int = 0
    tokensOut: int = 0


class ChatSession(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    userId: str
    title: str = "New Chat"
    model: str
    counters: SessionCounters = Field(default_factory=SessionCounters)
    lastMessageAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ChatMessage(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    sessionId: str
    userId: str
    role: str  # "user", "assistant", "system"
    content: str
    model: str
    tokens: TokenCount = Field(default_factory=TokenCount)
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Request/Response models


class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"
    model: Optional[str] = None


class CreateSessionResponse(BaseModel):
    sessionId: str
    title: str
    model: str
    createdAt: datetime


class SendMessageRequest(BaseModel):
    sessionId: str
    content: str
    model: Optional[str] = None


class SendMessageResponse(BaseModel):
    messageId: str
    sessionId: str
    role: str
    content: str
    model: str
    tokens: TokenCount
    createdAt: datetime


class GetSessionResponse(BaseModel):
    sessionId: str
    title: str
    model: str
    counters: SessionCounters
    lastMessageAt: Optional[datetime]
    createdAt: datetime
    updatedAt: datetime


class MessageHistoryItem(BaseModel):
    messageId: str
    role: str
    content: str
    tokens: TokenCount
    createdAt: datetime


class GetSessionHistoryResponse(BaseModel):
    session: GetSessionResponse
    messages: list[MessageHistoryItem]
