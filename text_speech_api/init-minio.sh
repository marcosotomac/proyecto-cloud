#!/bin/sh

# Script to initialize MinIO bucket for Text-to-Speech service
# This script creates the bucket and sets up the necessary policies

set -e

echo "🎤 Initializing MinIO bucket for Text-to-Speech service..."

# Wait for MinIO to be ready
until mc alias set myminio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}; do
  echo "Waiting for MinIO to be ready..."
  sleep 2
done

echo "✅ MinIO is ready"

# Create bucket if it doesn't exist
if mc ls myminio/${S3_BUCKET} 2>/dev/null; then
  echo "ℹ️  Bucket ${S3_BUCKET} already exists"
else
  echo "📦 Creating bucket ${S3_BUCKET}..."
  mc mb myminio/${S3_BUCKET}
  echo "✅ Bucket created"
fi

# Set bucket policy to allow read access (for signed URLs)
echo "🔐 Setting bucket policy..."
cat > /tmp/policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::${S3_BUCKET}/*"]
    }
  ]
}
EOF

mc anonymous set-json /tmp/policy.json myminio/${S3_BUCKET} || true

echo "✅ MinIO initialization complete for Text-to-Speech service"
echo "📍 Bucket: ${S3_BUCKET}"
echo "🌐 Endpoint: http://minio:9000"
