from __future__ import annotations

import json
from typing import Any, ClassVar, List, Optional

from redis.asyncio import Redis


class ReadOnlyAsyncCachedModel:
    """
    Read only async cached model
    """

    connection: ClassVar[Redis]
    ns: ClassVar[str]
    key_fields: ClassVar[List[str]]
    secondary_key_fields: ClassVar[List[str]]

    @classmethod
    def _prefix_key(cls, data: dict) -> str:
        key = cls.ns
        for _field in cls.key_fields:
            key += f":{data[_field]}"
        return key

    @classmethod
    def _secondary_prefix_key(cls, data: dict) -> str:
        key = f"{cls.ns}:_sk_"
        for _field in cls.secondary_key_fields:
            key += f":{data.get(_field, '*')}"
        return key

    @classmethod
    def _generate_key_pattern(cls, data: dict) -> str:
        pattern = cls.ns
        for _field in cls.key_fields:
            pattern += f":{data.get(_field, '*')}"
        return pattern

    @classmethod
    async def _get_matched_keys(cls, data: dict) -> List[str]:
        pattern = cls._generate_key_pattern(data)
        return await cls.connection.keys(pattern)

    @classmethod
    async def get(cls, **data: Any) -> Optional[dict]:
        key = cls._prefix_key(data)
        value: Any = await cls.connection.get(key)
        return json.loads(value) if value else None

    @classmethod
    async def get_by_secondary_key(cls, **data: Any) -> Optional[dict]:
        secondary_key = cls._secondary_prefix_key(data)
        primary_key = await cls.connection.get(secondary_key)
        if primary_key:
            value = await cls.connection.get(primary_key)
            return json.loads(value) if value else None

    @classmethod
    async def exists(cls, **data: Any) -> bool:
        key = cls._prefix_key(data)
        return await cls.connection.exists(key)  # type: ignore

    @classmethod
    async def get_count(cls, **data: Any) -> int:
        key: Any = cls._prefix_key(data)
        count: Optional[Any] = await cls.connection.get(key)
        return int(count) if count else 0

    @classmethod
    async def get_count_with_expiry(cls, **data):
        key = cls._prefix_key(data)
        pipe = cls.connection.pipeline()
        pipe.get(key)
        pipe.expiretime(key)
        count, expiry = await pipe.execute()
        return int(count) if count else 0, expiry

    @classmethod
    async def count_matched_keys(cls, in_batches=True, batch_size=1000, **data: Any) -> int:
        if not in_batches:
            keys = await cls._get_matched_keys(data)
            return len(keys)

        pattern = cls._generate_key_pattern(data)
        count = 0
        async for _ in cls.connection.scan_iter(match=pattern, count=batch_size):
            count += 1
            if count % batch_size == 0:
                print(f"Counted {count} keys till now...")
        print(f"Counted total {count} keys.")
        return count


class ReadWriteAsyncCachedModel(ReadOnlyAsyncCachedModel):
    """
    Read/Write async cached model
    """

    timeout: ClassVar[Optional[int]] = None

    @classmethod
    async def create(cls, **data: Any) -> str:
        key = cls._prefix_key(data)
        await cls.connection.set(key, json.dumps(data), ex=cls.timeout)
        return key

    @classmethod
    async def add_secondary_key(cls, primary_key: str, **data: Any) -> str:
        secondary_key = cls._secondary_prefix_key(data)
        await cls.connection.set(secondary_key, primary_key)
        return secondary_key

    @classmethod
    async def create_lookup(cls, **data: Any) -> str:
        key = cls._prefix_key(data)
        await cls.connection.set(key, 1, ex=cls.timeout)
        return key

    @classmethod
    async def create_counter(cls, starting=1, **data: Any) -> str:
        key = cls._prefix_key(data)
        await cls.connection.set(key, starting, ex=cls.timeout)
        return key

    @classmethod
    async def update(cls, **data):
        # key = cls._prefix_key(data)
        # NOTE: keepttl works only with Redis 6.0+
        # cls.connection.set(key, json.dumps(data), keepttl=True)
        await cls.create(**data)

    @classmethod
    async def increment(cls, amount=1, **data):
        key = cls._prefix_key(data)
        await cls.connection.incr(key, amount)

    @classmethod
    async def decrement(cls, amount=1, **data):
        key = cls._prefix_key(data)
        await cls.connection.decr(key, amount)

    @classmethod
    async def delete(cls, **data):
        key = cls._prefix_key(data)
        await cls.connection.delete(key)

    @classmethod
    async def delete_secondary_key(cls, **data: Any):
        secondary_key = cls._secondary_prefix_key(data)
        await cls.connection.delete(secondary_key)

    @classmethod
    async def delete_all(cls, in_batches=True, batch_size=1000, **data):
        if not in_batches:
            keys = await cls._get_matched_keys(data)
            if keys:
                await cls.connection.delete(*keys)
            return

        pattern = cls._generate_key_pattern(data)
        count = 0

        async with cls.connection.pipeline(transaction=False) as pipeline:
            async for key in cls.connection.scan_iter(match=pattern, count=batch_size):
                pipeline.delete(key)
                count += 1

                if count % batch_size == 0:
                    await pipeline.execute()
                    print(f"Deleted {count} keys till now...")

            if count % batch_size != 0:
                await pipeline.execute()
            print(f"Deleted total {count} keys.")

    @classmethod
    async def delete_all_secondary_keys(cls):
        secondary_keys = await cls.connection.keys(cls._secondary_prefix_key(data={}))
        if secondary_keys:
            await cls.connection.delete(*secondary_keys)


class ReadCachedHashAsyncModel(ReadWriteAsyncCachedModel):
    @classmethod
    async def get(cls, key, **data):
        ns_key = cls._prefix_key(data)
        return await cls.connection.hget(ns_key, key)

    @classmethod
    async def bulk_get(cls, keys, **data):
        ns_key = cls._prefix_key(data)
        return await cls.connection.hmget(ns_key, keys) if keys else []

    @classmethod
    async def get_all(cls, **data):
        ns_key = cls._prefix_key(data)
        return await cls.connection.hgetall(ns_key)


class ReadWriteCachedHashAsyncModel(ReadCachedHashAsyncModel):
    """
    Read/Write cached model for hashes
    """

    @classmethod
    async def add(cls, key, value, **data):
        ns_key = cls._prefix_key(data)
        await cls.connection.hset(ns_key, key=key, value=value)

    @classmethod
    async def bulk_add(cls, mapping, **data):
        ns_key = cls._prefix_key(data)
        await cls.connection.hset(ns_key, mapping=mapping)

    @classmethod
    async def remove(cls, key, **data):
        ns_key = cls._prefix_key(data)
        await cls.connection.hdel(ns_key, key)

    @classmethod
    async def bulk_remove(cls, keys, **data):
        ns_key = cls._prefix_key(data)
        await cls.connection.hdel(ns_key, *keys)
