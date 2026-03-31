import random
import string
from datetime import datetime, timedelta, UTC
from typing import Annotated, Literal, Any
from collections.abc import Callable, Coroutine
from uuid import UUID

from argon2 import PasswordHasher
from fastapi import Depends
from pydantic import ValidationError

from src.core.config import config
from src.database.repository import UserRepository
from src.database.repository.postgres.user.dtos import User
from src.exceptions import ClientError, NotFound, EmailAlreadyExists, SessionExpired, InvalidSessionData, \
    InvalidSessionType, InvalidCode, InvalidCredentials, InvalidToken
from src.integrations.redis import RedisClient
from src.services.auth.models import JWTTokens, JWTToken, SessionTypes, AuthRedisPrefixes, AuthSession
from src.services.security import JWTHandler
from src.services.ses import YandexSESService


class AuthService:
    def __init__(
        self,
        users_repository: Annotated[UserRepository, Depends(UserRepository)],
        email_service: Annotated[YandexSESService, Depends(YandexSESService)],
        redis_cache: Annotated[RedisClient, Depends(RedisClient)],
        jwt_handler: Annotated[JWTHandler, Depends(JWTHandler)],
    ):
        self._users_repository = users_repository
        self._email_service = email_service
        self._redis_cache = redis_cache
        self._password_hasher = PasswordHasher()
        self._jwt = jwt_handler

    @staticmethod
    def _generate_code() -> str:
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    def _get_expires_at(minutes: int = 10) -> datetime:
        return datetime.now(UTC) + timedelta(minutes=minutes)

    @staticmethod
    def _get_register_redis_key(email: str) -> str:
        return f'{AuthRedisPrefixes.registration_prefix}:{email}'

    @staticmethod
    def _get_login_redis_key(email: str) -> str:
        return f'{AuthRedisPrefixes.login_prefix}:{email}'

    @staticmethod
    def _get_password_reset_redis_key(email: str) -> str:
        return f'{AuthRedisPrefixes.password_reset_prefix}:{email}'

    # --------- REGISTER ---------
    async def start_registration(self, email: str, password: str) -> None:
        redis_key = self._get_register_redis_key(email)
        existing = await self._users_repository.get_by_email(email=email)
        if existing:
            raise EmailAlreadyExists

        await self._redis_cache.delete(redis_key)

        hashed_password = self._password_hasher.hash(password)
        code = self._generate_code()

        session = AuthSession(
            type=SessionTypes.register,
            email=email,
            password=hashed_password,
            code=code,
            expires_at=self._get_expires_at()
        )
        await self._redis_cache.set(redis_key, session.model_dump(), expire=config.AUTH_CACHE_TTL)
        await self._email_service.send_verification_email(user_email=email, token=code)

    async def complete_registration(self, email: str, password: str, code: str) -> JWTTokens:
        redis_key = self._get_register_redis_key(email)
        data = await self._redis_cache.get(redis_key)
        if not data:
            raise SessionExpired

        try:
            session = AuthSession.model_validate(data)
        except ValidationError as exc:
            raise InvalidSessionData from exc

        if session.type != SessionTypes.register:
            raise InvalidSessionType

        if session.code != code:
            raise InvalidCode

        if not self._password_hasher.verify(session.password, password):
            raise InvalidCredentials

        if session.expires_at < datetime.now(UTC):
            await self._redis_cache.delete(redis_key)
            raise ClientError(message="Code expired", code="code_expired")

        existing = await self._users_repository.get_by_email(email=email)
        if existing:
            raise EmailAlreadyExists

        user = await self._users_repository.create(
            entity=User(
                email=email,
                password_hash=session.password,
            ),
        )

        await self._redis_cache.delete(redis_key)
        return await self._create_tokens(user.id)

    # --------- LOGIN ---------
    async def start_login(self, email: str, password: str) -> None:
        redis_key = self._get_login_redis_key(email)
        user = await self._users_repository.get_by_email(email=email)
        if not user:
            raise InvalidCredentials

        try:
            self._password_hasher.verify(user.password_hash, password)
        except Exception as exc:
            raise InvalidCredentials from exc

        await self._redis_cache.delete(redis_key)

        code = self._generate_code()
        session = AuthSession(
            type=SessionTypes.login,
            email=email,
            code=code,
            expires_at=self._get_expires_at(),
        )
        await self._redis_cache.set(redis_key, session.model_dump(), expire=config.AUTH_CACHE_TTL)
        await self._email_service.send_verification_email(user_email=email, token=code)

    async def complete_login(self, email: str, password: str, code: str) -> JWTTokens:
        redis_key = self._get_login_redis_key(email)
        data = await self._redis_cache.get(redis_key)
        if not data:
            raise SessionExpired

        try:
            session = AuthSession.model_validate(data)
        except ValidationError as exc:
            raise InvalidSessionData from exc

        if session.type != SessionTypes.login:
            raise InvalidSessionType

        if session.code != code:
            raise InvalidCode

        if session.expires_at < datetime.now(UTC):
            await self._redis_cache.delete(redis_key)
            raise SessionExpired

        user = await self._users_repository.get_by_email(email=email)
        if not user:
            raise NotFound(message="User not found")

        try:
            self._password_hasher.verify(user.password_hash, password)
        except Exception as exc:
            raise InvalidCredentials from exc

        await self._redis_cache.delete(redis_key)
        return await self._create_tokens(user.id)

    # --------- RESET PASSWORD ---------
    async def start_password_reset(self, email: str, new_password: str) -> None:
        redis_key = self._get_password_reset_redis_key(email)
        user = await self._users_repository.get_by_email(email=email)
        if not user:
            raise NotFound(message="User with this email not found")

        await self._redis_cache.delete(redis_key)

        new_hashed = self._password_hasher.hash(new_password)
        code = self._generate_code()

        session = AuthSession(
            type=SessionTypes.reset_password,
            email=email,
            password=new_hashed,
            code=code,
            expires_at=self._get_expires_at()
        )
        await self._redis_cache.set(redis_key, session.model_dump(), expire=config.AUTH_CACHE_TTL)
        await self._email_service.send_verification_email(user_email=email, token=code)

    async def complete_password_reset(self, email: str, password: str, code: str) -> JWTTokens:
        redis_key = self._get_password_reset_redis_key(email)
        data = await self._redis_cache.get(redis_key)
        if not data:
            raise SessionExpired

        try:
            session = AuthSession.model_validate(data)
        except ValidationError as exc:
            raise InvalidSessionData from exc

        if session.type != SessionTypes.reset_password:
            raise InvalidSessionType

        if session.code != code:
            raise InvalidCode

        if not self._password_hasher.verify(session.password, password):
            raise InvalidCredentials

        if session.expires_at < datetime.now(UTC):
            await self._redis_cache.delete(redis_key)
            raise SessionExpired

        user = await self._users_repository.get_by_email(email=email)
        if not user:
            raise NotFound(message="User not found")

        user.password_hash = session.password
        await self._users_repository.update(user)

        await self._redis_cache.delete(redis_key)
        return await self._create_tokens(user.id)

    # --------- TWO-FACTOR DISPATCHER ---------
    async def complete_operation(
        self,
        operation: Literal['register', 'login', 'reset_password'],
        email: str,
        password: str,
        code: str,
    ) -> JWTTokens:
        mapping: dict[str, Callable[[str, str, str], Coroutine[Any, Any, JWTTokens]]] = {
            "register": self.complete_registration,
            "login": self.complete_login,
            "reset_password": self.complete_password_reset,
        }
        method = mapping.get(operation)
        if not method:
            raise ClientError(message="Invalid operation", code="invalid_operation")

        return await method(email, password, code)

    # --------- TOKENS ---------
    async def _create_tokens(self, user_id: UUID) -> JWTTokens:
        access_token, access_exp = self._jwt.get_access_token(user_id=user_id)
        refresh_token, refresh_exp = self._jwt.get_refresh_token(user_id=user_id)
        return JWTTokens(
            access=JWTToken(token=access_token, expires_at=access_exp),
            refresh=JWTToken(token=refresh_token, expires_at=refresh_exp)
        )

    async def refresh_tokens(self, refresh_token: str) -> JWTTokens:
        try:
            payload = self._jwt.decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise InvalidToken

            if self._jwt.is_token_expired(refresh_token):
                raise InvalidToken

            user_id = payload.get("sub")
            if not user_id:
                raise InvalidToken

            return await self._create_tokens(UUID(user_id))
        except Exception as exc:
            raise InvalidToken from exc

    async def verify_token(self, token: str) -> tuple[User, datetime, str]:
        try:
            payload = self._jwt.decode_token(token)
            if not payload or "sub" not in payload:
                raise InvalidToken

            if self._jwt.is_token_expired(token):
                raise InvalidToken

            user_id = payload["sub"]
            user = await self._users_repository.get_by_id(UUID(user_id))
            if not user:
                raise NotFound(message="User not found")

            expiration = self._jwt.get_token_expiration(token)
            return user, expiration, payload.get("type", "access")
        except Exception as exc:
            raise InvalidToken from exc
