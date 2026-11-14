"""S3 object storage (RustFS locally and on EC2)."""

from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack
from typing import Any, NamedTuple

import aioboto3
from botocore.config import Config

from src.config import settings

STREAM_CHUNK_SIZE = 256 * 1024

_session = aioboto3.Session()


class ObjectStream(NamedTuple):
    content_type: str
    content_range: str | None
    body: AsyncGenerator[bytes]


def _client():  # noqa: ANN202
    return _session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY.get_secret_value(),
        region_name="us-east-1",
        # RustFS/MinIO serve buckets as paths, not subdomains.
        config=Config(s3={"addressing_style": "path"}),
    )


async def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    async with _client() as s3:
        await s3.put_object(
            Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type
        )


async def open_object_stream(key: str, range_header: str | None = None) -> ObjectStream:
    """Stream an object, or a Range of it. The client stays open until the body
    is fully read, so the body can go straight into a StreamingResponse.

    Raises botocore's ClientError, e.g. NoSuchKey or InvalidRange.
    """
    stack = AsyncExitStack()
    s3 = await stack.enter_async_context(_client())
    try:
        params: dict[str, Any] = {"Bucket": settings.S3_BUCKET, "Key": key}
        if range_header:
            params["Range"] = range_header
        response = await s3.get_object(**params)
    except BaseException:
        await stack.aclose()
        raise

    async def body() -> AsyncGenerator[bytes]:
        try:
            async for chunk in response["Body"].iter_chunks(STREAM_CHUNK_SIZE):
                yield chunk
        finally:
            await stack.aclose()

    return ObjectStream(
        content_type=response.get("ContentType") or "application/octet-stream",
        content_range=response.get("ContentRange"),
        body=body(),
    )
