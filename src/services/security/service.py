from datetime import datetime, UTC, timedelta
from typing import Any, Literal
from jose import jwt
from uuid import UUID

from src.core.config import config


class JWTHandler:
    """Handler for JWT tokens"""

    def get_access_token(self, user_id: UUID) -> tuple[str, datetime]:
        return self._create_jwt_token(user_id, "access", expires_at=datetime.now(UTC) + timedelta(minutes=config.ACCESS_TOKEN_EXP_MIN))

    def get_refresh_token(self, user_id: UUID) -> tuple[str, datetime]:
        return self._create_jwt_token(user_id, "refresh", expires_at=datetime.now(UTC) + timedelta(minutes=config.REFRESH_TOKEN_EXP_MIN))

    @staticmethod
    def _create_jwt_token(user_id: UUID, token_type: Literal['access', 'refresh'], expires_at: datetime) -> tuple[str, datetime]:
        """Create jwt token"""
        jwt_data = {
            'sub': str(user_id),
            'type': token_type,
            'exp': int(expires_at.timestamp()),
        }

        token = jwt.encode(jwt_data, config.JWT_SECRET.get_secret_value(), algorithm=config.JWT_ALGORITHM)
        return token, expires_at

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        """Decode JWT token"""
        return jwt.decode(token, config.JWT_SECRET.get_secret_value(), algorithms=[config.JWT_ALGORITHM])

    @staticmethod
    def is_token_expired(token: str | dict[str, Any]) -> bool:
        try:
            payload = JWTHandler.decode_token(token) if isinstance(token, str) else token
            exp = payload.get('exp')
            if not exp:
                return True

            return exp < int(datetime.now(UTC).timestamp())

        except Exception:
            return True

    @staticmethod
    def get_token_expiration(token: str) -> datetime:
        """Get token expiration time"""
        payload = JWTHandler.decode_token(token)
        exp = payload.get('exp')
        if not exp:
            raise ValueError('Token has no expiration time')

        return datetime.fromtimestamp(exp, tz=UTC)
