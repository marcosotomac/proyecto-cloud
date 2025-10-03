import boto3
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from app.config import settings


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region
        )
        self.bucket = settings.s3_bucket

    async def ensure_bucket_exists(self):
        """Asegura que el bucket existe, lo crea si no existe"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                self.client.create_bucket(Bucket=self.bucket)
            else:
                raise

    def put_json(self, key: str, data: Dict[Any, Any]) -> str:
        """Guarda un objeto JSON en S3"""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )
            print(f"✅ Guardado JSON en S3: {key}")
            return key
        except Exception as e:
            print(f"❌ Error guardando JSON {key}: {e}")
            raise

    def put_bytes(self, key: str, data: bytes, content_type: str = 'application/octet-stream') -> str:
        """Guarda bytes en S3"""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            print(f"✅ Guardado bytes en S3: {key} ({len(data)} bytes)")
            return key
        except Exception as e:
            print(f"❌ Error guardando bytes {key}: {e}")
            raise

    def get_object(self, key: str) -> bytes:
        """Obtiene un objeto de S3"""
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()

    def get_json(self, key: str) -> Dict[Any, Any]:
        """Obtiene y parsea un JSON de S3"""
        data = self.get_object(key)
        return json.loads(data.decode())

    def try_get_object(self, key: str) -> Optional[bytes]:
        """Intenta obtener un objeto, retorna None si no existe"""
        try:
            return self.get_object(key)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def generate_signed_url(self, key: str, expiration: int = 300) -> str:
        """Genera una URL firmada para acceso temporal"""
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expiration
        )
