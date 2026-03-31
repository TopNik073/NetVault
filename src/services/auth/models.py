from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime



class JWTToken(BaseModel):
    token: str
    expires_at: datetime

class JWTTokens(BaseModel):
    access: JWTToken
    refresh: JWTToken

class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(..., alias='accessToken')
    refresh_token: str = Field(..., alias='refreshToken')

class SessionTypes(StrEnum):
    register= 'register'
    login = 'login'
    reset_password= 'reset_password'

class AuthSession(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: SessionTypes
    email: str
    password: str | None = None
    code: str
    expires_at: datetime

class AuthRedisPrefixes:
    base_prefix = 'auth'
    registration_prefix = f'{base_prefix}:register'
    login_prefix = f'{base_prefix}:login'
    password_reset_prefix = f'{base_prefix}:password_reset'