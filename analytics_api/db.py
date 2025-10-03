from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from models import ServiceType, EventType, TimeRange
import logging

logger = logging.getLogger(__name__)


class AnalyticsDatabase:
    """MongoDB client for analytics data"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.events_collection = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client.get_default_database()
            self.events_collection = self.db.analytics_events

            # Create indexes for better query performance
            await self.events_collection.create_index("user_id")
            await self.events_collection.create_index("service_type")
            await self.events_collection.create_index("event_type")
            await self.events_collection.create_index("timestamp")
            await self.events_collection.create_index([("user_id", 1), ("timestamp", -1)])
            await self.events_collection.create_index([("service_type", 1), ("timestamp", -1)])

            logger.info("Connected to MongoDB and created indexes")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def track_event(self, event_data: Dict[str, Any]) -> str:
        """
        Track an analytics event

        Args:
            event_data: Event data to store

        Returns:
            Event ID
        """
        try:
            result = await self.events_collection.insert_one(event_data)
            logger.info(f"Tracked event: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            raise

    async def get_user_analytics(
        self,
        user_id: Optional[str],
        time_range: TimeRange = TimeRange.ALL,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific user

        Args:
            user_id: User ID (None for anonymous)
            time_range: Time range for analytics
            start_date: Custom start date (optional)
            end_date: Custom end date (optional)

        Returns:
            Analytics data
        """
        try:
            # Build query
            query = {"user_id": user_id}

            # Add time filter
            if start_date or end_date:
                time_filter = {}
                if start_date:
                    time_filter["$gte"] = start_date
                if end_date:
                    time_filter["$lte"] = end_date
                query["timestamp"] = time_filter
            elif time_range != TimeRange.ALL:
                query["timestamp"] = {
                    "$gte": self._get_time_range_start(time_range)}

            # Aggregation pipeline
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "successful_requests": {
                            "$sum": {"$cond": [{"$eq": ["$event_type", EventType.SUCCESS.value]}, 1, 0]}
                        },
                        "failed_requests": {
                            "$sum": {"$cond": [{"$eq": ["$event_type", EventType.ERROR.value]}, 1, 0]}
                        },
                        "llm_chat_requests": {
                            "$sum": {"$cond": [{"$eq": ["$service_type", ServiceType.LLM_CHAT.value]}, 1, 0]}
                        },
                        "image_generation_requests": {
                            "$sum": {"$cond": [{"$eq": ["$service_type", ServiceType.TEXT_TO_IMAGE.value]}, 1, 0]}
                        },
                        "speech_generation_requests": {
                            "$sum": {"$cond": [{"$eq": ["$service_type", ServiceType.TEXT_TO_SPEECH.value]}, 1, 0]}
                        },
                        "total_input_tokens": {"$sum": {"$ifNull": ["$metadata.input_tokens", 0]}},
                        "total_output_tokens": {"$sum": {"$ifNull": ["$metadata.output_tokens", 0]}},
                        "total_storage_bytes": {"$sum": {"$ifNull": ["$metadata.size_bytes", 0]}},
                        "avg_response_time_ms": {"$avg": "$metadata.response_time_ms"},
                        "first_request": {"$min": "$timestamp"},
                        "last_request": {"$max": "$timestamp"}
                    }
                }
            ]

            result = await self.events_collection.aggregate(pipeline).to_list(1)

            if result:
                data = result[0]
                data.pop("_id", None)
                data["total_tokens"] = data.get(
                    "total_input_tokens", 0) + data.get("total_output_tokens", 0)
                data["success_rate"] = (
                    (data.get("successful_requests", 0) /
                     data.get("total_requests", 1)) * 100
                    if data.get("total_requests", 0) > 0 else 0.0
                )
                return data

            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0
            }

        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            raise

    async def get_service_analytics(
        self,
        service_type: ServiceType,
        time_range: TimeRange = TimeRange.ALL
    ) -> Dict[str, Any]:
        """Get analytics for a specific service"""
        try:
            query = {"service_type": service_type.value}

            if time_range != TimeRange.ALL:
                query["timestamp"] = {
                    "$gte": self._get_time_range_start(time_range)}

            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "successful_requests": {
                            "$sum": {"$cond": [{"$eq": ["$event_type", EventType.SUCCESS.value]}, 1, 0]}
                        },
                        "failed_requests": {
                            "$sum": {"$cond": [{"$eq": ["$event_type", EventType.ERROR.value]}, 1, 0]}
                        },
                        "unique_users": {"$addToSet": "$user_id"},
                        "avg_response_time_ms": {"$avg": "$metadata.response_time_ms"}
                    }
                }
            ]

            result = await self.events_collection.aggregate(pipeline).to_list(1)

            if result:
                data = result[0]
                unique_users = data.get("unique_users", [])
                anonymous_count = unique_users.count(None)

                return {
                    "service_type": service_type.value,
                    "total_requests": data.get("total_requests", 0),
                    "successful_requests": data.get("successful_requests", 0),
                    "failed_requests": data.get("failed_requests", 0),
                    "success_rate": (
                        (data.get("successful_requests", 0) /
                         data.get("total_requests", 1)) * 100
                        if data.get("total_requests", 0) > 0 else 0.0
                    ),
                    "unique_users": len(unique_users) - anonymous_count,
                    "anonymous_users": anonymous_count,
                    "avg_response_time_ms": data.get("avg_response_time_ms")
                }

            return {
                "service_type": service_type.value,
                "total_requests": 0,
                "unique_users": 0
            }

        except Exception as e:
            logger.error(f"Failed to get service analytics: {e}")
            raise

    async def get_system_analytics(
        self,
        time_range: TimeRange = TimeRange.ALL,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get system-wide analytics"""
        try:
            query = {}
            if time_range != TimeRange.ALL:
                query["timestamp"] = {
                    "$gte": self._get_time_range_start(time_range)}

            # Overall stats
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "unique_users": {"$addToSet": "$user_id"},
                        "start_date": {"$min": "$timestamp"},
                        "end_date": {"$max": "$timestamp"}
                    }
                }
            ]

            overall = await self.events_collection.aggregate(pipeline).to_list(1)

            # Service breakdown
            services = []
            for service_type in ServiceType:
                service_data = await self.get_service_analytics(service_type, time_range)
                services.append(service_data)

            # Top users
            top_users_pipeline = [
                {"$match": query},
                {"$match": {"user_id": {"$ne": None}}},
                {"$group": {"_id": "$user_id", "request_count": {"$sum": 1}}},
                {"$sort": {"request_count": -1}},
                {"$limit": limit}
            ]

            top_users = await self.events_collection.aggregate(top_users_pipeline).to_list(limit)
            top_users_list = [
                {"user_id": user["_id"],
                    "request_count": user["request_count"]}
                for user in top_users
            ]

            if overall:
                data = overall[0]
                unique_users = data.get("unique_users", [])
                anonymous_count = unique_users.count(None)

                return {
                    "total_requests": data.get("total_requests", 0),
                    "total_users": len(unique_users) - anonymous_count,
                    "total_anonymous_requests": anonymous_count,
                    "services": services,
                    "top_users": top_users_list,
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date")
                }

            return {
                "total_requests": 0,
                "total_users": 0,
                "services": services,
                "top_users": []
            }

        except Exception as e:
            logger.error(f"Failed to get system analytics: {e}")
            raise

    async def get_usage_stats(
        self,
        user_id: Optional[str] = None,
        time_range: TimeRange = TimeRange.WEEK
    ) -> Dict[str, Any]:
        """Get detailed usage statistics"""
        try:
            query = {}
            if user_id is not None:
                query["user_id"] = user_id

            if time_range != TimeRange.ALL:
                query["timestamp"] = {
                    "$gte": self._get_time_range_start(time_range)}

            # Requests by period (hour or day)
            group_format = "%Y-%m-%d" if time_range in [
                TimeRange.WEEK, TimeRange.MONTH] else "%Y-%m-%d-%H"

            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "period": {"$dateToString": {"format": group_format, "date": "$timestamp"}},
                            "service": "$service_type"
                        },
                        "count": {"$sum": 1},
                        "success_count": {
                            "$sum": {"$cond": [{"$eq": ["$event_type", EventType.SUCCESS.value]}, 1, 0]}
                        }
                    }
                }
            ]

            results = await self.events_collection.aggregate(pipeline).to_list(None)

            requests_by_period = {}
            requests_by_service = {}
            success_rate_by_service = {}

            for result in results:
                period = result["_id"]["period"]
                service = result["_id"]["service"]
                count = result["count"]
                success_count = result["success_count"]

                requests_by_period[period] = requests_by_period.get(
                    period, 0) + count
                requests_by_service[service] = requests_by_service.get(
                    service, 0) + count

                if service not in success_rate_by_service:
                    success_rate_by_service[service] = {
                        "total": 0, "success": 0}
                success_rate_by_service[service]["total"] += count
                success_rate_by_service[service]["success"] += success_count

            # Calculate success rates
            for service in success_rate_by_service:
                total = success_rate_by_service[service]["total"]
                success = success_rate_by_service[service]["success"]
                success_rate_by_service[service] = (
                    success / total * 100) if total > 0 else 0.0

            return {
                "time_range": time_range.value,
                "user_id": user_id,
                "requests_by_period": requests_by_period,
                "requests_by_service": requests_by_service,
                "success_rate_by_service": success_rate_by_service
            }

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise

    def _get_time_range_start(self, time_range: TimeRange) -> datetime:
        """Get start datetime for a time range"""
        now = datetime.utcnow()

        if time_range == TimeRange.HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            return now - timedelta(days=30)
        elif time_range == TimeRange.YEAR:
            return now - timedelta(days=365)
        else:
            return datetime.min


# Global database instance
db = AnalyticsDatabase()
