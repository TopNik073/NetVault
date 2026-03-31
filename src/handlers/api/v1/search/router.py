from typing import Literal, Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Depends

from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.search.models import SearchResponse, BaseBucketsResponse, BaseFilesResponse, BaseFolderResponse
from src.handlers.dependencies.auth import get_current_user
from src.services.search.service import SearchService

search_router = APIRouter(prefix='/search', tags=['search'])


@search_router.get('', response_model=SearchResponse)
async def global_search(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SearchService, Depends(SearchService)],
    query: str = Query(..., description='Search query', min_length=1),
    search_type: Literal['bucket', 'folder', 'file'] | None = Query(None, alias='type', description='Filter by type'),
    bucket_id: UUID | None = Query(None, alias='bucketId', description='Limit search to specific bucket'),  # noqa: B008
) -> SearchResponse:
    buckets, folders, files = await service.search(
        user_id=user.id,
        query=query,
        search_type=search_type,
        bucket_id=bucket_id,
    )

    return SearchResponse(
        buckets=[
            BaseBucketsResponse(
                id=b.id,
                name=b.name,
                isPublic=b.is_public,
                filesCount=b.files_count,
                size=b.size,
            )
            for b in buckets
        ],
        folders=[
            BaseFolderResponse(
                id=f.id,
                name=f.name,
                depth=f.depth,
                bucketId=f.bucket_id,
                parentId=f.parent_id,
            )
            for f in folders
        ],
        files=[
            BaseFilesResponse(
                id=f.id,
                name=f.original_filename,
                bucketId=str(f.bucket_id),
                folderId=str(f.folder_id) if f.folder_id else '',
                size=f.file_size_bytes,
                mimeType=f.mime_type or '',
                uploadedAt=f.created_at,
            )
            for f in files
        ],
    )
