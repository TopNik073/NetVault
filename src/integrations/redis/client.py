from typing import Any, Annotated

from fastapi.params import Depends
from redis.asyncio import Redis
import json

from src.core.config import config
from src.exceptions import RedisException
from src.integrations.redis.connection import get_redis



class RedisClient:
    def __init__(
        self,
        redis_client: Annotated[Redis, Depends(get_redis)],
    ):
        self._redis = redis_client

    async def get(self, key: str) -> dict[str, Any] | None:
        value = await self._redis.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RedisException from exc

    async def set(self, key: str, value: dict[str, Any], expire: int | None = config.CACHE_TTL) -> None:
        if value is None:
            return

        data = json.dumps(value, default=str)

        if expire:
            await self._redis.setex(key, expire, data)
        else:
            await self._redis.set(key, data)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0

    async def update(self, key: str, value: Any, expire: int = config.CACHE_TTL) -> None:
        await self.set(key, value, expire=expire)

    async def hset(self, key: str, mapping: dict) -> None:
        await self._redis.hset(key, mapping=mapping)

    async def hgetall(self, key: str) -> dict:
        return await self._redis.hgetall(key)

    async def hget(self, key: str, field: str) -> Any:
        return await self._redis.hget(key, field)

    async def sadd(self, key: str, *values) -> int:
        return await self._redis.sadd(key, *values)

    async def scard(self, key: str) -> int:
        return await self._redis.scard(key)

    async def sismember(self, key: str, value) -> bool:
        return bool(await self._redis.sismember(key, value))

    async def expire(self, key: str, seconds: int) -> None:
        await self._redis.expire(key, seconds)
