"""S3 client for Text-to-Speech history storage"""
import json
import boto3
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for TTS history management"""

    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region
        )
        self.bucket = settings.s3_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.info(f"Creating bucket {self.bucket}")
                self.s3.create_bucket(Bucket=self.bucket)
            else:
                logger.error(f"Error checking bucket: {e}")
                raise

    def save_tts_history(
        self,
        request_id: str,
        user_id: Optional[str],
        username: Optional[str],
        prompt: str,
        audio_bytes: bytes,
        model: str,
        voice: str,
        provider: str,
        latency_ms: int,
        status_code: int = 200,
        cost_usd: float = 0.0,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Save TTS generation history to S3

        Structure:
        requests/{yyyy}/{mm}/{dd}/{id}/
          ├─ input.json       # Request parameters
          ├─ record.json      # Complete metadata
          └─ audio/output.mp3 # Generated audio

        Returns:
            Dictionary with S3 keys
        """
        now = datetime.utcnow()
        yyyy = now.strftime("%Y")
        mm = now.strftime("%m")
        dd = now.strftime("%d")

        base_path = f"requests/{yyyy}/{mm}/{dd}/{request_id}"

        # Prepare paths
        input_key = f"{base_path}/input.json"
        record_key = f"{base_path}/record.json"
        audio_key = f"{base_path}/audio/output.mp3"

        # 1. Save input.json
        input_data = {
            "prompt": prompt,
            "model": model,
            "voice": voice
        }
        self.s3.put_object(
            Bucket=self.bucket,
            Key=input_key,
            Body=json.dumps(input_data, indent=2),
            ContentType="application/json"
        )
        logger.info(f"Saved input: {input_key}")

        # 2. Save audio file
        self.s3.put_object(
            Bucket=self.bucket,
            Key=audio_key,
            Body=audio_bytes,
            ContentType="audio/mpeg"
        )
        logger.info(f"Saved audio: {audio_key} ({len(audio_bytes)} bytes)")

        # 3. Save record.json
        record_data = {
            "id": request_id,
            "userId": user_id,
            "username": username,
            "service": "tts",
            "provider": provider,
            "model": model,
            "voice": voice,
            "prompt": prompt,
            "status": status_code,
            "latencyMs": latency_ms,
            "cost": {"usd": cost_usd},
            "artifacts": {
                "audio": audio_key,
                "input": input_key
            },
            "createdAt": now.isoformat() + "Z",
            "meta": meta or {}
        }
        self.s3.put_object(
            Bucket=self.bucket,
            Key=record_key,
            Body=json.dumps(record_data, indent=2),
            ContentType="application/json"
        )
        logger.info(f"Saved record: {record_key}")

        # 4. Optional: Add to user history index
        if user_id:
            self._append_user_history(user_id, request_id, now, prompt, voice)

        return {
            "input": input_key,
            "record": record_key,
            "audio": audio_key
        }

    def _append_user_history(
        self,
        user_id: str,
        request_id: str,
        timestamp: datetime,
        prompt: str,
        voice: str
    ):
        """Append entry to user's daily history index"""
        yyyy = timestamp.strftime("%Y")
        mm = timestamp.strftime("%m")
        dd = timestamp.strftime("%d")

        index_key = f"users/{user_id}/tts/history/{yyyy}/{mm}/{dd}.jsonl"

        # Create index entry
        entry = {
            "id": request_id,
            "ts": timestamp.isoformat() + "Z",
            "prompt": prompt[:100],  # Truncate for index
            "voice": voice
        }

        try:
            # Append to existing file or create new
            self.s3.put_object(
                Bucket=self.bucket,
                Key=index_key,
                Body=json.dumps(entry) + "\n",
                ContentType="application/x-ndjson"
            )
            logger.info(f"Updated user history: {index_key}")
        except Exception as e:
            logger.warning(f"Failed to update user history: {e}")

    def get_record(self, request_id: str, date: datetime) -> Optional[Dict[str, Any]]:
        """Retrieve record.json for a request"""
        yyyy = date.strftime("%Y")
        mm = date.strftime("%m")
        dd = date.strftime("%d")

        record_key = f"requests/{yyyy}/{mm}/{dd}/{request_id}/record.json"

        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=record_key)
            return json.loads(response['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Record not found: {record_key}")
                return None
            raise

    def get_signed_url(self, key: str, expires_in: int = 300) -> str:
        """Generate a signed URL for downloading"""
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise

    def list_user_audios(
        self,
        user_id: str,
        limit: int = 10,
        prefix: Optional[str] = None
    ) -> list:
        """List user's TTS generations (from history index)"""
        # This would typically scan the user's history JSONL files
        # For now, simplified implementation
        prefix = prefix or f"users/{user_id}/tts/history/"

        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=limit
            )

            objects = response.get('Contents', [])
            return [obj['Key'] for obj in objects]
        except ClientError as e:
            logger.error(f"Failed to list user audios: {e}")
            return []


# Global instance
s3_client = S3Client()
