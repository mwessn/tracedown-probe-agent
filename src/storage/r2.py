"""R2/S3-compatible body storage — for object-storage deployments."""

from __future__ import annotations

import logging
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig

from storage.base import BodyStorage

log = logging.getLogger(__name__)

SCHEME = "s3://"


class R2Storage(BodyStorage):
    """Stores bodies in Cloudflare R2 (or any S3-compatible store).

    Storage URIs use the ``s3://`` scheme: ``s3://{bucket}/{key}``.
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        prefix: str = "",
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix.rstrip("/")
        self._endpoint_url = endpoint_url
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=BotoConfig(
                region_name="auto",
                signature_version="s3v4",
            ),
        )

    def _full_key(self, key: str) -> str:
        """Prepend the configured prefix to a key."""
        if self._prefix:
            return f"{self._prefix}/{key}"
        return key

    def upload(self, local_path: Path, key: str) -> str:
        """Upload a file to R2/S3.

        Returns an ``s3://`` URI, e.g. ``s3://my-bucket/prefix/call_0.json``.
        """
        full_key = self._full_key(key)
        self._client.upload_file(str(local_path), self._bucket, full_key)
        uri = f"{SCHEME}{self._bucket}/{full_key}"
        log.debug("uploaded %s → %s", local_path.name, uri)
        return uri

    def download_url(self, uri: str) -> str | None:
        """Generate a presigned download URL (1 hour expiry)."""
        bucket, key = _parse_uri(uri)
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )


def _parse_uri(uri: str) -> tuple[str, str]:
    """Parse ``s3://bucket/key`` into (bucket, key)."""
    if uri.startswith(SCHEME):
        uri = uri[len(SCHEME):]
    parts = uri.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid S3 URI: {uri}")
    return parts[0], parts[1]
