from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends


from src.database.repository.postgres.user.dtos import User
from src.handlers.api.v1.buckets.models import (
    GetBucketsResponse,
    BaseBucketsResponse,
    CreateBucketsRequest,
    UpdateBucketsRequest,
    GrantBucketPermissionResponse,
    GrantBucketPermissionRequest,
    UpdateBucketPermissionResponse,
    UpdateBucketPermissionRequest,
    DeleteBucketPermissionResponse,
    DeleteBucketPermissionRequest,
    GetUsersWithPermissionResponse,
)
from src.handlers.dependencies.auth import get_current_user
from src.services.buckets.service import BucketsService

buckets_router = APIRouter(prefix='/buckets', tags=['buckets'])


@buckets_router.get('/', response_model=GetBucketsResponse)
async def get_buckets(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
) -> GetBucketsResponse:
    buckets = await service.get_buckets(user_id=user.id)
    return GetBucketsResponse.model_validate([BaseBucketsResponse.from_bucket(bucket) for bucket in buckets])


@buckets_router.post('/', response_model=BaseBucketsResponse)
async def create_bucket(
    payload: CreateBucketsRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
) -> BaseBucketsResponse:
    bucket = await service.create_bucket(
        user_id=user.id,
        name=payload.name,
        is_public=payload.is_public,
    )

    return BaseBucketsResponse.from_bucket(bucket)


@buckets_router.get('/{bucketId}')
async def get_bucket(
    bucketId: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
):
    bucket = await service.get_bucket(
        user_id=user.id,
        bucket_id=bucketId,
    )

    return BaseBucketsResponse.from_bucket(bucket)


@buckets_router.put('/{bucketId}')
async def update_bucket(
    bucketId: UUID,
    payload: UpdateBucketsRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
):
    bucket = await service.update_bucket(
        user_id=user.id,
        bucket_id=bucketId,
        name=payload.name,
        is_public=payload.is_public,
    )

    return BaseBucketsResponse.from_bucket(bucket)


@buckets_router.delete('/{bucketId}')
async def delete_bucket(
    bucketId: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
):
    return await service.delete_bucket(
        user_id=user.id,
        bucket_id=bucketId,
    )


@buckets_router.get('/{bucketId}/users', response_model=GetUsersWithPermissionResponse)
async def get_bucket_users(
    bucketId: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
) -> GetUsersWithPermissionResponse:
    users = await service.get_bucket_users(
        actor_user_id=user.id,
        bucket_id=bucketId,
    )

    return GetUsersWithPermissionResponse.model_validate(users)


@buckets_router.post('/{bucketId}/permissions', response_model=GrantBucketPermissionResponse)
async def grant_bucket_permissions(
    bucketId: UUID,
    payload: GrantBucketPermissionRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
) -> GrantBucketPermissionResponse:
    permission = await service.grant_permission(
        actor_user_id=user.id,
        bucket_id=bucketId,
        email=payload.email,
        target_user_id=payload.user_id,
        permission=payload.permission,
    )

    return GrantBucketPermissionResponse.from_permission(permission)


@buckets_router.put('/{bucketId}/permissions', response_model=UpdateBucketPermissionResponse)
async def update_bucket_permissions(
    bucketId: UUID,
    payload: UpdateBucketPermissionRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
) -> UpdateBucketPermissionResponse:
    permission = await service.update_permission(
        actor_user_id=user.id,
        bucket_id=bucketId,
        email=payload.email,
        target_user_id=payload.user_id,
        permission=payload.permission,
    )

    return UpdateBucketPermissionResponse.from_permission(permission)


@buckets_router.delete('/{bucketId}/permissions', response_model=DeleteBucketPermissionResponse)
async def delete_bucket_permissions(
    bucketId: UUID,
    payload: DeleteBucketPermissionRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[BucketsService, Depends(BucketsService)],
) -> DeleteBucketPermissionResponse:
    await service.delete_permission(
        actor_user_id=user.id,
        bucket_id=bucketId,
        email=payload.email,
        target_user_id=payload.user_id,
    )

    return DeleteBucketPermissionResponse()
