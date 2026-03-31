from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RestorePasswordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    new_password: str = Field(..., alias='newPassword', min_length=6)

class RestorePasswordResponse(BaseModel):
    ...