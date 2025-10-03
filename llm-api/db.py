from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB and create indices"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]

            # Create indices for chat_sessions
            await self.db.chat_sessions.create_index(
                [("userId", ASCENDING), ("updatedAt", DESCENDING)],
                name="userId_updatedAt"
            )
            await self.db.chat_sessions.create_index(
                [("userId", ASCENDING), ("createdAt", DESCENDING)],
                name="userId_createdAt"
            )
            await self.db.chat_sessions.create_index(
                [("_id", ASCENDING), ("userId", ASCENDING)],
                name="id_userId"
            )

            # Create indices for chat_messages
            await self.db.chat_messages.create_index(
                [("sessionId", ASCENDING), ("createdAt", ASCENDING)],
                name="sessionId_createdAt"
            )
            await self.db.chat_messages.create_index(
                [("userId", ASCENDING), ("createdAt", DESCENDING)],
                name="userId_createdAt"
            )
            await self.db.chat_messages.create_index(
                [("sessionId", ASCENDING), ("role", ASCENDING)],
                name="sessionId_role"
            )

            logger.info(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

    # Chat Sessions CRUD
    async def create_session(self, user_id: str, title: str, model: str) -> str:
        """Create a new chat session"""
        session = {
            "userId": user_id,
            "title": title,
            "model": model,
            "counters": {
                "messages": 0,
                "tokensIn": 0,
                "tokensOut": 0
            },
            "lastMessageAt": None,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        result = await self.db.chat_sessions.insert_one(session)
        return str(result.inserted_id)

    async def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID and user ID"""
        try:
            session = await self.db.chat_sessions.find_one({
                "_id": ObjectId(session_id),
                "userId": user_id
            })
            if session:
                session["_id"] = str(session["_id"])
            return session
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    async def update_session_counters(
        self,
        session_id: str,
        user_id: str,
        increment_messages: int = 1,
        increment_tokens_in: int = 0,
        increment_tokens_out: int = 0
    ):
        """Update session counters"""
        await self.db.chat_sessions.update_one(
            {"_id": ObjectId(session_id), "userId": user_id},
            {
                "$inc": {
                    "counters.messages": increment_messages,
                    "counters.tokensIn": increment_tokens_in,
                    "counters.tokensOut": increment_tokens_out
                },
                "$set": {
                    "lastMessageAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
            }
        )

    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List user's chat sessions"""
        cursor = self.db.chat_sessions.find({"userId": user_id}).sort([
            ("updatedAt", DESCENDING)
        ]).skip(skip).limit(limit)

        sessions = []
        async for session in cursor:
            session["_id"] = str(session["_id"])
            sessions.append(session)
        return sessions

    # Chat Messages CRUD
    async def create_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0
    ) -> str:
        """Create a new chat message"""
        message = {
            "sessionId": session_id,
            "userId": user_id,
            "role": role,
            "content": content,
            "model": model,
            "tokens": {
                "input": tokens_in,
                "output": tokens_out
            },
            "createdAt": datetime.utcnow()
        }
        result = await self.db.chat_messages.insert_one(message)
        return str(result.inserted_id)

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        cursor = self.db.chat_messages.find({"sessionId": session_id}).sort([
            ("createdAt", ASCENDING)
        ]).skip(skip).limit(limit)

        messages = []
        async for message in cursor:
            message["_id"] = str(message["_id"])
            messages.append(message)
        return messages


# Global MongoDB client instance
mongo_client = MongoDBClient()
