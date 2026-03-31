from pydantic import BaseModel, EmailStr, Field

from src.services.auth.models import TokenResponse


class TwoFaRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    code: str = Field(..., min_length=6, max_length=6)

class TwoFaResponse(TokenResponse):
    ...