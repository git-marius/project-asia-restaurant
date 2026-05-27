import os
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.client import Config


@dataclass(frozen=True)
class S3Config:
    """Gebündelte S3/MinIO-Konfiguration aus Environment-Variablen."""

    bucket: str
    endpoint_url: str
    public_endpoint_url: str
    region: str
    access_key_id: str
    secret_access_key: str
    presigned_expires_seconds: int


def get_s3_config() -> S3Config:
    """Liest S3/MinIO-Zugangsdaten und Endpoints aus der Umgebung."""
    endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")

    return S3Config(
        bucket=os.getenv("S3_BUCKET", "restaurant-videos"),
        endpoint_url=endpoint_url,
        public_endpoint_url=os.getenv("S3_PUBLIC_ENDPOINT_URL", "http://localhost:9000"),
        region=os.getenv("S3_REGION", "eu-central-1"),
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        presigned_expires_seconds=int(os.getenv("S3_PRESIGNED_URL_EXPIRES_SECONDS", "300")),
    )


def _client(config: S3Config, *, public_endpoint: bool = False):
    """Erstellt einen S3-Client; für presigned URLs wird der Browser-Endpoint genutzt."""
    endpoint_url = config.public_endpoint_url if public_endpoint else config.endpoint_url
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=config.region,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def upload_video_file(path: Path, *, object_key: str, content_type: str = "video/mp4") -> str:
    """Lädt eine lokale Videodatei in den privaten S3-Bucket hoch."""
    config = get_s3_config()
    _client(config).upload_file(
        str(path),
        config.bucket,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )
    return config.bucket


def create_presigned_video_url(bucket: str, object_key: str) -> str:
    """Erzeugt eine kurzlebige URL, über die der Browser das private Video abspielen kann."""
    config = get_s3_config()
    return _client(config, public_endpoint=True).generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=config.presigned_expires_seconds,
    )
