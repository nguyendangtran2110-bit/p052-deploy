from __future__ import annotations

import inspect
from typing import Any

import aioboto3

from src.backend.core.config import Settings
from src.backend.domain.common.errors import ConfigurationError


class S3Storage:
    """Small S3 adapter for presigned browser upload/download URLs."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = aioboto3.Session()

    async def create_presigned_upload(self, object_key: str, mime_type: str) -> str:
        self._ensure_configured()
        params = {
            "Bucket": self.settings.aws_s3_bucket_name,
            "Key": object_key,
            "ContentType": mime_type,
        }
        async with self.session.client("s3", **self._client_kwargs()) as client:
            return await self._maybe_await(
                client.generate_presigned_url(
                    "put_object",
                    Params=params,
                    ExpiresIn=self.settings.s3_presigned_url_expire_seconds,
                )
            )

    async def create_presigned_download(self, object_key: str, filename: str) -> str:
        self._ensure_configured()
        params = {
            "Bucket": self.settings.aws_s3_bucket_name,
            "Key": object_key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        }
        async with self.session.client("s3", **self._client_kwargs()) as client:
            return await self._maybe_await(
                client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=self.settings.s3_presigned_url_expire_seconds,
                )
            )

    def _ensure_configured(self) -> None:
        if not self.settings.aws_s3_bucket_name:
            raise ConfigurationError("S3 attachment storage is not configured")

    def _client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.settings.aws_region:
            kwargs["region_name"] = self.settings.aws_region
        if self.settings.aws_access_key_id:
            kwargs["aws_access_key_id"] = self.settings.aws_access_key_id
        if self.settings.aws_secret_access_key:
            kwargs["aws_secret_access_key"] = self.settings.aws_secret_access_key
        if self.settings.aws_s3_endpoint_url:
            kwargs["endpoint_url"] = self.settings.aws_s3_endpoint_url
        return kwargs

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        return await value if inspect.isawaitable(value) else value
