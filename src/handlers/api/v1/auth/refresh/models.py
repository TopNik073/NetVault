from pydantic import BaseModel, Field

from src.services.auth.models import TokenResponse


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., alias="refreshToken")

class RefreshResponse(TokenResponse):
    ...