import json
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from app.exceptions.errors import S3StorageError
from app.models.document import KnowledgeChunk


class S3Service:
    def __init__(self, raw_bucket: str, enriched_bucket: str, region: str) -> None:
        self.raw_bucket, self.enriched_bucket = raw_bucket, enriched_bucket
        self.client = boto3.client("s3", region_name=region)

    @staticmethod
    def uri(bucket: str, key: str) -> str:
        return f"s3://{bucket}/{key.lstrip('/')}"

    @staticmethod
    def parse_uri(uri: str) -> tuple[str, str]:
        parsed = urlparse(uri)
        if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.strip("/"):
            raise S3StorageError("Invalid S3 URI")
        return parsed.netloc, parsed.path.lstrip("/")

    def raw_key(self, source_type: str, file_name: str, document_id: str) -> str:
        path = PurePosixPath(file_name)
        return f"raw/{source_type}/{document_id}/{path.name}"

    def chunk_key(self, chunk: KnowledgeChunk) -> str:
        source_type = str(chunk.metadata["source_type"])
        return f"enriched/{source_type}/{chunk.document_id}/chunks/chunk-{chunk.sequence:04d}.txt"

    def chunk_prefix_uri(self, source_type: str, document_id: str) -> str:
        return self.uri(self.enriched_bucket, f"enriched/{source_type}/{document_id}/chunks/")

    def upload_raw(self, source: bytes, source_type: str, file_name: str, document_id: str, content_type: str | None) -> str:
        key = self.raw_key(source_type, file_name, document_id)
        self.client.put_object(Bucket=self.raw_bucket, Key=key, Body=source, ContentType=content_type or "application/octet-stream")
        return self.uri(self.raw_bucket, key)

    def read_uri(self, source_uri: str) -> bytes:
        bucket, key = self.parse_uri(source_uri)
        try:
            return self.client.get_object(Bucket=bucket, Key=key)["Body"].read()
        except ClientError as error:
            raise S3StorageError("Unable to read source object") from error

    def object_exists(self, bucket: str, key: str) -> bool:
        return self.get_object_metadata(bucket, key) is not None

    def get_object_metadata(self, bucket: str, key: str) -> dict[str, Any] | None:
        try:
            return self.client.head_object(Bucket=bucket, Key=key)
        except ClientError:
            return None

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        paginator = self.client.get_paginator("list_objects_v2")
        return [item["Key"] for page in paginator.paginate(Bucket=bucket, Prefix=prefix) for item in page.get("Contents", []) if not item["Key"].endswith("/")]

    def upload_chunk(self, chunk: KnowledgeChunk) -> str:
        key = self.chunk_key(chunk)
        self.client.put_object(Bucket=self.enriched_bucket, Key=key, Body=chunk.content.encode("utf-8"), ContentType="text/plain; charset=utf-8")
        return self.uri(self.enriched_bucket, key)

    def upload_sidecar(self, destination_uri: str, sidecar: dict[str, Any]) -> None:
        bucket, key = self.parse_uri(destination_uri)
        sidecar_key = f"{key}.metadata.json"
        self.client.put_object(Bucket=bucket, Key=sidecar_key, Body=json.dumps(sidecar).encode(), ContentType="application/json")
