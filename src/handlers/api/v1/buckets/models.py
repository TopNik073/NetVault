from uuid import UUID

from pydantic import BaseModel, RootModel, Field, EmailStr, model_validator, ValidationError

from src.database.repository.postgres.bucket_permission.dtos import PermissionType, BucketPermission
from src.database.repository.postgres.bucket.dtos import Bucket
from src.services.buckets.models import UserBrief


class CreateBucketsRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_public: bool = Field(..., alias='isPublic')


class UpdateBucketsRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_public: bool = Field(..., alias='isPublic')


class BaseBucketsResponse(BaseModel):
    id: UUID
    name: str
    isPublic: bool
    permission: PermissionType | None = None
    filesCount: int = 0
    size: int = 0

    @classmethod
    def from_bucket(cls, bucket: 'Bucket') -> 'BaseBucketsResponse':
        return cls(
            id=bucket.id,
            name=bucket.name,
            isPublic=bucket.is_public,
            permission=bucket.permission,
            filesCount=bucket.files_count,
            size=bucket.size,
        )


class GetBucketsResponse(RootModel[list[BaseBucketsResponse]]): ...


# PERMISSIONS
class GrantBucketPermissionRequest(BaseModel):
    email: EmailStr | None = None
    user_id: UUID | None = None
    permission: PermissionType

    @model_validator(mode='after')
    def validate(self):
        if not self.email and not self.user_id:
            raise ValidationError('Either email or user_id must be provided')
        if self.email and self.user_id:
            raise ValidationError('Email and user_id are mutually exclusive')
        return self


class GrantBucketPermissionResponse(BaseModel):
    user_id: UUID
    permission: PermissionType

    @classmethod
    def from_permission(cls, perm: 'BucketPermission') -> 'GrantBucketPermissionResponse':
        return cls(
            user_id=perm.user_id,
            permission=perm.permission_type,
        )


class UpdateBucketPermissionRequest(BaseModel):
    email: EmailStr | None = None
    user_id: UUID | None = None
    permission: PermissionType

    @model_validator(mode='after')
    def validate(self):
        if not self.email and not self.user_id:
            raise ValidationError('Either email or user_id must be provided')
        if self.email and self.user_id:
            raise ValidationError('Email and user_id are mutually exclusive')
        return self


class UpdateBucketPermissionResponse(BaseModel):
    user_id: UUID
    permission: PermissionType

    @classmethod
    def from_permission(cls, perm: BucketPermission) -> 'UpdateBucketPermissionResponse':
        return cls(
            user_id=perm.user_id,
            permission=perm.permission_type,
        )


class DeleteBucketPermissionRequest(BaseModel):
    email: EmailStr | None = None
    user_id: UUID | None = None

    @model_validator(mode='after')
    def validate(self):
        if not self.email and not self.user_id:
            raise ValidationError('Either email or user_id must be provided')
        if self.email and self.user_id:
            raise ValidationError('Email and user_id are mutually exclusive')
        return self


class DeleteBucketPermissionResponse(BaseModel): ...


class GetUsersWithPermissionResponse(RootModel[list[UserBrief]]): ...
