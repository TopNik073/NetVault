import asyncio
from datetime import datetime, timedelta, UTC

import aioboto3
from minio import Minio
from minio.datatypes import Bucket
from botocore.config import Config as BotoConfig

from src.core.config import config


class MinioClient:
    def __init__(self):
        self._client = Minio(
            endpoint=config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY.get_secret_value(),
            secure=config.MINIO_SECURE,
            region=config.MINIO_REGION,
        )

        self._external_endpoint = config.MINIO_EXTERNAL_ENDPOINT
        if self._external_endpoint:
            self._external_for_sign = Minio(
                endpoint=self._external_endpoint,
                access_key=config.MINIO_ACCESS_KEY,
                secret_key=config.MINIO_SECRET_KEY.get_secret_value(),
                secure=config.MINIO_SECURE,
                region=config.MINIO_REGION,
            )
        else:
            self._external_for_sign = self._client

        self._boto3_session = aioboto3.Session(
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY.get_secret_value(),
            region_name=config.MINIO_REGION,
        )
        self._boto3_config = BotoConfig(
            signature_version='s3v4',
            s3={'addressing_style': 'path'},
        )

    async def list_buckets(self) -> list[Bucket]:
        buckets = await asyncio.to_thread(self._client.list_buckets)
        return list(buckets)

    async def create_bucket(self, bucket_name: str) -> None:
        await asyncio.to_thread(self._client.make_bucket, bucket_name)

    async def delete_bucket_objects(self, bucket_name: str) -> None:
        objects = await asyncio.to_thread(self._client.list_objects, bucket_name, recursive=True)
        for obj in objects:
            await asyncio.to_thread(self._client.remove_object, bucket_name, obj.object_name)

    async def delete_bucket(self, bucket_name: str) -> None:
        await asyncio.to_thread(self._client.remove_bucket, bucket_name)

    async def delete_object(self, bucket_name: str, object_name: str) -> None:
        await asyncio.to_thread(self._client.remove_object, bucket_name, object_name)

    async def get_presigned_download_url(
        self, bucket_name: str, object_name: str, expires_in: int = 3600
    ) -> tuple[str, datetime]:
        url = await asyncio.to_thread(
            self._external_for_sign.presigned_get_object,
            bucket_name,
            object_name,
            expires=timedelta(seconds=expires_in),
        )

        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        return url, expires_at

    async def delete_objects(self, bucket_name: str, object_names: list[str]) -> None:
        for object_name in object_names:
            await self.delete_object(bucket_name, object_name)

    async def presigned_put_object(
        self, bucket_name: str, object_name: str, expires: timedelta = timedelta(hours=1)
    ) -> str:
        return await asyncio.to_thread(
            self._external_for_sign.presigned_put_object,
            bucket_name,
            object_name,
            expires=expires,
        )

    async def create_multipart_upload(self, bucket_name: str, object_name: str) -> str:
        return await asyncio.to_thread(
            self._client._create_multipart_upload,  # noqa: SLF001
            bucket_name,
            object_name,
            {},
        )

    async def presigned_put_part_url(
        self,
        bucket_name: str,
        object_name: str,
        upload_id: str,
        part_number: int,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        endpoint = self._external_endpoint or config.MINIO_ENDPOINT
        scheme = 'https' if config.MINIO_SECURE else 'http'
        endpoint_url = f'{scheme}://{endpoint}'

        expires_seconds = int(expires.total_seconds())

        async with self._boto3_session.client(
            's3',
            endpoint_url=endpoint_url,
            config=self._boto3_config,
        ) as client:
            return await client.generate_presigned_url(
                ClientMethod='upload_part',
                HttpMethod='PUT',
                Params={
                    'Bucket': bucket_name,
                    'Key': object_name,
                    'UploadId': upload_id,
                    'PartNumber': part_number,
                },
                ExpiresIn=expires_seconds,
            )

    async def complete_multipart_upload(
        self,
        bucket_name: str,
        object_name: str,
        upload_id: str,
        parts: list[dict],
    ) -> None:
        endpoint = self._external_endpoint or config.MINIO_ENDPOINT
        scheme = 'https' if config.MINIO_SECURE else 'http'
        endpoint_url = f'{scheme}://{endpoint}'

        s3_parts = [{'ETag': p['ETag'].strip('"'), 'PartNumber': p['PartNumber']} for p in parts]

        async with self._boto3_session.client(
            's3',
            endpoint_url=endpoint_url,
            config=self._boto3_config,
        ) as client:
            await client.complete_multipart_upload(
                Bucket=bucket_name,
                Key=object_name,
                UploadId=upload_id,
                MultipartUpload={'Parts': s3_parts},
            )

    async def abort_multipart_upload(
        self,
        bucket_name: str,
        object_name: str,
        upload_id: str,
    ) -> None:
        endpoint = self._external_endpoint or config.MINIO_ENDPOINT
        scheme = 'https' if config.MINIO_SECURE else 'http'
        endpoint_url = f'{scheme}://{endpoint}'

        async with self._boto3_session.client(
            's3',
            endpoint_url=endpoint_url,
            config=self._boto3_config,
        ) as client:
            await client.abort_multipart_upload(
                Bucket=bucket_name,
                Key=object_name,
                UploadId=upload_id,
            )

    async def stat_object(self, bucket_name: str, object_name: str) -> dict:
        obj = await asyncio.to_thread(self._client.stat_object, bucket_name, object_name)

        return {
            'size': obj.size,
            'etag': obj.etag,
            'last_modified': obj.last_modified,
            'content_type': obj.content_type,
        }
