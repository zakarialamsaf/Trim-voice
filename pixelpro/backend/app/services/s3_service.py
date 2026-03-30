"""
S3 service with local filesystem fallback for development.

When AWS_ACCESS_KEY_ID == "dev" (set in .env.local), all uploads and downloads
use LOCAL_STORAGE_DIR instead of real S3/MinIO. Presigned URLs become
/static/<key> served by the FastAPI static files mount.
"""
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

_USE_LOCAL = settings.AWS_ACCESS_KEY_ID == "dev"

if not _USE_LOCAL:
    _s3_kwargs = dict(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    if settings.AWS_ENDPOINT_URL:
        _s3_kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    s3_client = boto3.client("s3", **_s3_kwargs)
else:
    s3_client = None
    Path(settings.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using local file storage at {settings.LOCAL_STORAGE_DIR}")


def generate_s3_key(user_id: str, image_id: str, suffix: str, ext: str) -> str:
    return f"users/{user_id}/{image_id}/{suffix}.{ext}"


def _local_path(s3_key: str) -> Path:
    p = Path(settings.LOCAL_STORAGE_DIR) / s3_key
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def upload_file_to_s3(
    file_bytes: bytes,
    s3_key: str,
    bucket: str,
    content_type: str = "image/png",
) -> str:
    if _USE_LOCAL:
        _local_path(s3_key).write_bytes(file_bytes)
        return s3_key
    try:
        s3_client.put_object(
            Bucket=bucket, Key=s3_key, Body=file_bytes, ContentType=content_type
        )
        return s3_key
    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        raise


def get_presigned_url(
    s3_key: str,
    bucket: str,
    expiry: int = settings.S3_PRESIGNED_URL_EXPIRY,
) -> str:
    if _USE_LOCAL:
        # Served by the /static mount added in main.py
        return f"http://localhost:8000/static/{s3_key}"
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiry,
        )
        if settings.AWS_ENDPOINT_URL and "minio:" in settings.AWS_ENDPOINT_URL:
            url = url.replace("http://minio:9000", "http://localhost:9000")
        return url
    except ClientError as e:
        logger.error(f"Presigned URL generation failed: {e}")
        raise


def download_file_from_s3(s3_key: str, bucket: str) -> bytes:
    if _USE_LOCAL:
        p = _local_path(s3_key)
        if not p.exists():
            raise FileNotFoundError(f"Local file not found: {p}")
        return p.read_bytes()
    try:
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        return response["Body"].read()
    except ClientError as e:
        logger.error(f"S3 download failed: {e}")
        raise


def delete_s3_object(s3_key: str, bucket: str) -> None:
    if _USE_LOCAL:
        p = _local_path(s3_key)
        if p.exists():
            p.unlink()
        return
    try:
        s3_client.delete_object(Bucket=bucket, Key=s3_key)
    except ClientError as e:
        logger.error(f"S3 delete failed: {e}")
