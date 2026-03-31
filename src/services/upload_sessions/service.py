import uuid
from datetime import datetime, timedelta, UTC
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.core.config import config
from src.database.repository import (
    UserRepository,
    BucketRepository,
    FolderRepository,
    BucketPermissionRepository,
    FileRepository,
)
from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.database.repository.postgres.file.dtos import File
from src.exceptions import ClientError, NotFound, PermissionDenied
from src.handlers.api.v1.upload_sessions.models import (
    InitUploadResponse,
    SimpleUploadResponse,
    MultipartUploadResponse,
    UploadStatusResponse,
    CompleteUploadResponse,
)
from src.integrations.minio.client import MinioClient

from src.integrations.redis import RedisClient


class UploadSessionsService:
    def __init__(  # noqa: PLR0913
        self,
        users_repository: Annotated[UserRepository, Depends(UserRepository)],
        buckets_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        folders_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        bucket_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
        files_repository: Annotated[FileRepository, Depends(FileRepository)],
        minio_client: Annotated[MinioClient, Depends(MinioClient)],
        redis_client: Annotated[RedisClient, Depends(RedisClient)],
    ):
        self._users_repo = users_repository
        self._buckets_repo = buckets_repository
        self._folders_repo = folders_repository
        self._perms_repo = bucket_permission_repository
        self._files_repo = files_repository
        self._minio = minio_client
        self._redis = redis_client

        self._threshold = config.UPLOAD_THRESHOLD
        self._chunk_size = config.UPLOAD_CHUNK_SIZE

    async def _check_bucket_access(self, user_id: UUID, bucket_id: UUID, required_permission: PermissionType) -> None:
        bucket = await self._buckets_repo.get_by_id(bucket_id)
        if not bucket:
            raise NotFound('Bucket not found')

        if bucket.owner_id == user_id:
            return

        if bucket.is_public and required_permission == PermissionType.READ:
            return

        permission = await self._perms_repo.get_by_bucket_and_user(bucket_id, user_id)
        if not permission:
            raise PermissionDenied('Access denied to this bucket')

        rank = {PermissionType.READ: 1, PermissionType.WRITE: 2, PermissionType.ADMIN: 3}
        if rank[permission.permission_type] < rank[required_permission]:
            raise PermissionDenied('Insufficient permissions')

    async def _build_file_path(self, folder_id: UUID | None, filename: str) -> str:
        if folder_id is None:
            return filename

        path_parts = []
        current_id = folder_id
        while current_id:
            folder = await self._folders_repo.get_by_id(current_id)
            if not folder:
                break
            path_parts.insert(0, folder.name)
            current_id = folder.parent_id
        path_parts.append(filename)
        return '/'.join(path_parts)

    async def _check_folder(self, folder_id: UUID | None, bucket_id: UUID) -> None:
        if folder_id is None:
            return
        folder = await self._folders_repo.get_by_id(folder_id)
        if not folder:
            raise NotFound('Folder not found')
        if folder.bucket_id != bucket_id:
            raise ClientError('Folder does not belong to the specified bucket')

    async def _reserve_quota(self, user_id: UUID, size: int) -> None:
        user = await self._users_repo.get_by_id(user_id)
        if not user:
            raise NotFound('User not found')
        if user.storage_used_bytes + user.storage_reserved_bytes + size > user.storage_quota_bytes:
            raise ClientError('Insufficient storage quota')
        user.storage_reserved_bytes += size
        await self._users_repo.update(user)

    async def _release_quota(self, user_id: UUID, size: int) -> None:
        user = await self._users_repo.get_by_id(user_id)
        if user:
            user.storage_reserved_bytes -= size
            await self._users_repo.update(user)

    async def _apply_quota(self, user_id: UUID, size: int) -> None:
        user = await self._users_repo.get_by_id(user_id)
        if user:
            user.storage_reserved_bytes -= size
            user.storage_used_bytes += size
            await self._users_repo.update(user)

    async def _get_bucket_name(self, bucket_id: UUID) -> str:
        bucket = await self._buckets_repo.get_by_id(bucket_id)
        if not bucket:
            raise NotFound('Bucket not found')
        return bucket.minio_bucket_name

    async def init_upload(  # noqa: PLR0913
        self,
        actor_user_id: UUID,
        bucket_id: UUID,
        folder_id: UUID | None,
        name: str,
        size: int,
        mime_type: str,
    ) -> InitUploadResponse:
        await self._check_bucket_access(actor_user_id, bucket_id, PermissionType.WRITE)
        await self._check_folder(folder_id, bucket_id)

        await self._reserve_quota(actor_user_id, size)

        object_name = f'{uuid.uuid4()}/{name}'

        session_id = uuid.uuid4()
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        path = await self._build_file_path(folder_id, name)

        if size < self._threshold:
            url = await self._minio.presigned_put_object(
                bucket_name=await self._get_bucket_name(bucket_id),
                object_name=object_name,
                expires=timedelta(hours=24),
            )
            meta = {
                'type': 'simple',
                'user_id': str(actor_user_id),
                'bucket_id': str(bucket_id),
                'folder_id': str(folder_id) if folder_id else 'None',
                'name': name,
                'path': path,
                'object_name': object_name,
                'size': size,
                'mime_type': mime_type,
                'status': 'pending',
                'expires_at': expires_at.isoformat(),
            }
            await self._redis.hset(f'upload:{session_id}:meta', mapping=meta)
            await self._redis.expire(f'upload:{session_id}:meta', 86400)

            return SimpleUploadResponse(
                sessionId=session_id,
                uploadType='simple',
                uploadUrl=url,
                expiresAt=expires_at,
            )
        bucket_name = await self._get_bucket_name(bucket_id)
        total_parts = (size + self._chunk_size - 1) // self._chunk_size
        try:
            upload_id = await self._minio.create_multipart_upload(bucket_name, object_name)
        except Exception:
            await self._release_quota(actor_user_id, size)
            raise

        part_urls = {}
        for i in range(1, total_parts + 1):
            url = await self._minio.presigned_put_part_url(
                bucket_name=bucket_name,
                object_name=object_name,
                upload_id=upload_id,
                part_number=i,
                expires=timedelta(hours=24),
            )
            part_urls[i] = url

        meta = {
            'type': 'multipart',
            'user_id': str(actor_user_id),
            'bucket_id': str(bucket_id),
            'folder_id': str(folder_id) if folder_id else 'None',
            'name': name,
            'path': path,
            'object_name': object_name,
            'size': size,
            'mime_type': mime_type,
            'upload_id': upload_id,
            'total_parts': total_parts,
            'chunk_size': self._chunk_size,
            'status': 'active',
            'expires_at': expires_at.isoformat(),
        }
        await self._redis.hset(f'upload:{session_id}:meta', mapping=meta)
        await self._redis.expire(f'upload:{session_id}:meta', 86400)
        await self._redis.hset(f'upload:{session_id}:etags', mapping={'_init': '1'})
        await self._redis.expire(f'upload:{session_id}:etags', 86400)

        return MultipartUploadResponse(
            sessionId=session_id,
            uploadType='multipart',
            partUrls=part_urls,
            chunkSize=self._chunk_size,
            totalParts=total_parts,
            expiresAt=expires_at,
        )

    async def complete_part(self, actor_user_id: UUID, session_id: UUID, part_number: int, etag: str) -> None:
        meta = await self._redis.hgetall(f'upload:{session_id}:meta')
        if not meta:
            raise NotFound('Upload session not found')

        if meta.get('type') != 'multipart':
            raise ClientError('This operation is only for multipart uploads')

        if UUID(meta['user_id']) != actor_user_id:
            raise PermissionDenied('Access denied')

        if meta['status'] != 'active':
            raise ClientError('Session is not active')

        await self._redis.sadd(f'upload:{session_id}:parts', part_number)
        await self._redis.hset(f'upload:{session_id}:etags', {str(part_number): etag})

    async def get_upload_status(self, actor_user_id: UUID, session_id: UUID) -> UploadStatusResponse:
        meta = await self._redis.hgetall(f'upload:{session_id}:meta')
        if not meta:
            raise NotFound('Upload session not found')

        if UUID(meta['user_id']) != actor_user_id:
            raise PermissionDenied('Access denied')

        expires_at = datetime.fromisoformat(meta['expires_at'])
        if meta['type'] == 'simple':
            return UploadStatusResponse(
                sessionId=session_id,
                uploadType='simple',
                status=meta['status'],
                expiresAt=expires_at,
                completedParts=None,
                totalParts=None,
            )
        completed_parts = await self._redis.scard(f'upload:{session_id}:parts')
        return UploadStatusResponse(
            sessionId=session_id,
            uploadType='multipart',
            status=meta['status'],
            completedParts=completed_parts,
            totalParts=int(meta['total_parts']),
            expiresAt=expires_at,
        )

    async def complete_upload(self, actor_user_id: UUID, session_id: UUID) -> CompleteUploadResponse:
        meta = await self._redis.hgetall(f'upload:{session_id}:meta')
        if not meta:
            raise NotFound('Upload session not found')

        if UUID(meta['user_id']) != actor_user_id:
            raise PermissionDenied('Access denied')

        bucket_name = await self._get_bucket_name(UUID(meta['bucket_id']))
        folder_id = None
        if meta.get('folder_id') and meta['folder_id'] != 'None':
            folder_id = UUID(meta['folder_id'])

        if meta['type'] == 'simple':
            if meta['status'] != 'pending':
                raise ClientError('Invalid session status')

            try:
                await self._minio.stat_object(bucket_name, meta['object_name'])
            except Exception as exc:
                raise ClientError('File not uploaded to storage') from exc

            file = File(
                original_filename=meta['name'],
                bucket_id=UUID(meta['bucket_id']),
                folder_id=folder_id,
                owner_id=actor_user_id,
                file_size_bytes=int(meta['size']),
                mime_type=meta['mime_type'],
                storage_filename=meta['object_name'],
                path=meta['path'],
                file_hash=None,
            )
            created = await self._files_repo.create(file)

            await self._apply_quota(actor_user_id, created.file_size_bytes)

            await self._redis.delete(f'upload:{session_id}:meta')

            return CompleteUploadResponse(
                fileId=created.id,
                name=created.original_filename,
                size=created.file_size_bytes,
                mimeType=created.mime_type,
                bucketId=created.bucket_id,
                folderId=created.folder_id,
                uploadedAt=created.created_at,
            )
        if meta['status'] != 'active':
            raise ClientError('Invalid session status', code='invalid_session_data')

        total_parts = int(meta['total_parts'])
        completed_parts = await self._redis.scard(f'upload:{session_id}:parts')
        if completed_parts != total_parts:
            raise ClientError('Not all parts uploaded', code='not_all_parts_uploaded')

        etags = await self._redis.hgetall(f'upload:{session_id}:etags')
        parts = []
        for i in range(1, total_parts + 1):
            etag = etags.get(str(i))
            if not etag:
                raise ClientError(f'Missing etag for part {i}')
            parts.append({'PartNumber': i, 'ETag': etag})

        await self._minio.complete_multipart_upload(
            bucket_name=bucket_name,
            object_name=meta['object_name'],
            upload_id=meta['upload_id'],
            parts=parts,
        )

        file = File(
            original_filename=meta['name'],
            bucket_id=UUID(meta['bucket_id']),
            folder_id=folder_id,
            owner_id=actor_user_id,
            file_size_bytes=int(meta['size']),
            mime_type=meta['mime_type'],
            storage_filename=meta['object_name'],
            path=meta['path'],
            file_hash=None,
        )
        created = await self._files_repo.create(file)

        await self._apply_quota(actor_user_id, created.file_size_bytes)

        for key in [
            f'upload:{session_id}:meta',
            f'upload:{session_id}:parts',
            f'upload:{session_id}:etags',
        ]:
            await self._redis.delete(key)

        return CompleteUploadResponse(
            fileId=created.id,
            name=created.original_filename,
            size=created.file_size_bytes,
            mimeType=created.mime_type,
            bucketId=created.bucket_id,
            folderId=created.folder_id,
            uploadedAt=created.created_at,
        )

    async def abort_upload(self, actor_user_id: UUID, session_id: UUID) -> None:
        meta = await self._redis.hgetall(f'upload:{session_id}:meta')
        if not meta:
            raise NotFound('Upload session not found')

        if UUID(meta['user_id']) != actor_user_id:
            raise PermissionDenied('Access denied')

        if meta['type'] == 'multipart' and meta['status'] == 'active':
            bucket_name = await self._get_bucket_name(UUID(meta['bucket_id']))
            await self._minio.abort_multipart_upload(
                bucket_name=bucket_name,
                object_name=meta['object_name'],
                upload_id=meta['upload_id'],
            )

        await self._release_quota(actor_user_id, int(meta['size']))

        for key in [
            f'upload:{session_id}:meta',
            f'upload:{session_id}:parts',
            f'upload:{session_id}:etags',
        ]:
            await self._redis.delete(key)
