from uuid import UUID

from pydantic import BaseModel, RootModel

from src.database.repository.postgres.bucket_permission.dtos import PermissionType
from src.database.repository.postgres.folder.dtos import Folder


class BaseFolderResponse(BaseModel):
    id: UUID
    name: str
    depth: int
    bucketId: UUID
    parentId: UUID | None
    permission: PermissionType | None = None

    @classmethod
    def from_folder(cls, folder: Folder) -> 'BaseFolderResponse':
        return cls(
            id=folder.id,
            name=folder.name,
            depth=folder.depth,
            bucketId=folder.bucket_id,
            parentId=folder.parent_id,
            permission=folder.permission,
        )


class GetFoldersResponse(RootModel[list[BaseFolderResponse]]):
    pass


class GetFolderInfoResponse(BaseFolderResponse):
    pass


class CreateFolderRequest(BaseModel):
    name: str
    bucketId: UUID
    parentId: UUID | None


class CreateFolderResponse(BaseFolderResponse):
    pass


class RenameFolderRequest(BaseModel):
    name: str


class RenameFolderResponse(BaseFolderResponse):
    pass


class MoveFolderRequest(BaseModel):
    parentId: UUID | None


class MoveFolderResponse(BaseFolderResponse):
    pass


class DeleteFolderResponse(BaseModel):
    pass
