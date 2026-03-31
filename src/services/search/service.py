from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends

from src.database.repository import BucketRepository, FolderRepository, FileRepository, BucketPermissionRepository
from src.database.repository.postgres.bucket.dtos import Bucket
from src.database.repository.postgres.file.dtos import File
from src.database.repository.postgres.folder.dtos import Folder
from src.exceptions import PermissionDenied


class SearchService:
    def __init__(
        self,
        bucket_repository: Annotated[BucketRepository, Depends(BucketRepository)],
        folder_repository: Annotated[FolderRepository, Depends(FolderRepository)],
        file_repository: Annotated[FileRepository, Depends(FileRepository)],
        bucket_permission_repository: Annotated[BucketPermissionRepository, Depends(BucketPermissionRepository)],
    ):
        self._bucket_repository = bucket_repository
        self._folder_repository = folder_repository
        self._file_repository = file_repository
        self._bucket_permission_repository = bucket_permission_repository

    async def _get_accessible_bucket_ids(self, user_id: UUID, bucket_id: UUID | None = None) -> list[UUID]:
        accessible = await self._bucket_repository.get_accessible_buckets(user_id)
        accessible_ids = [b.id for b in accessible]

        if bucket_id:
            if bucket_id not in accessible_ids:
                raise PermissionDenied('Bucket not accessible')
            return [bucket_id]
        return accessible_ids

    async def search(
        self,
        user_id: UUID,
        query: str,
        search_type: Literal['bucket', 'folder', 'file'] | None = None,
        bucket_id: UUID | None = None,
    ) -> tuple[list[Bucket], list[Folder], list[File]]:
        bucket_ids = await self._get_accessible_bucket_ids(user_id, bucket_id)

        buckets: list[Bucket] = []
        folders: list[Folder] = []
        files: list[File] = []

        bucket_stats = {}
        if bucket_ids:
            bucket_stats = await self._file_repository.get_buckets_stats(bucket_ids)

        if (search_type is None or search_type == 'bucket') and bucket_id is None:
            buckets = await self._bucket_repository.search_by_name(bucket_ids, query)
            for bucket in buckets:
                if bucket.id in bucket_stats:
                    bucket.files_count, bucket.size = bucket_stats[bucket.id]

        if search_type is None or search_type == 'folder':
            folders = await self._folder_repository.search_by_name(bucket_ids, query)

        if search_type is None or search_type == 'file':
            files = await self._file_repository.search_by_name(bucket_ids, query)

        return buckets, folders, files
