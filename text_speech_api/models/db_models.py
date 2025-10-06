"""
Database models for Text-to-Speech API.
"""
from sqlalchemy import Column, String, Integer, Text, DECIMAL, BigInteger, TIMESTAMP, JSON
from sqlalchemy.sql import func
from db import Base


class TTSConversion(Base):
    """
    Model for storing TTS conversion records.
    Tracks all text-to-speech conversions with metadata.
    """
    __tablename__ = "tts_conversions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    text = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=False)
    model = Column(String(100), default="pollinations")
    voice = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    duration_seconds = Column(DECIMAL(10, 2), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    s3_key = Column(String(500), nullable=False)
    s3_bucket = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(),
                        nullable=False, index=True)
    # Use column name 'metadata' but attribute 'extra_metadata'
    extra_metadata = Column("metadata", JSON, nullable=True)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "audio_url": self.audio_url,
            "model": self.model,
            "voice": self.voice,
            "language": self.language,
            "duration_seconds": float(self.duration_seconds) if self.duration_seconds else None,
            "file_size_bytes": self.file_size_bytes,
            "s3_key": self.s3_key,
            "s3_bucket": self.s3_bucket,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_metadata
        }
