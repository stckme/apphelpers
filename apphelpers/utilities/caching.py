from __future__ import annotations

import json
from typing import (
    Any,
    ClassVar,
    List,
    Optional,
)

from redis import Redis


class ReadOnlyCachedModel:
    """
    Read only cached model
    """

    connection: ClassVar[Redis]
    ns: ClassVar[str]
    key_fields: ClassVar[List[str]]

    @classmethod
    def prefix_key(cls, data: dict) -> str:
        key = cls.ns
        for _field in cls.key_fields:
            key += f":{data[_field]}"
        return key

    @classmethod
    def get(cls, **data: Any) -> Optional[dict]:
        key = cls.prefix_key(data)
        value: Any = cls.connection.get(key)
        return json.loads(value) if value else None

    @classmethod
    def exists(cls, **data: Any) -> bool:
        key = cls.prefix_key(data)
        return cls.connection.exists(key)  # type: ignore

    @classmethod
    def get_count(cls, **data: Any) -> int:
        key: Any = cls.prefix_key(data)
        count: Optional[Any] = cls.connection.get(key)
        return int(count) if count else 0

    @classmethod
    def count_matched_keys(cls, **data) -> int:
        keys = cls._get_matched_keys(data)
        return len(keys)


class ReadWriteCachedModel(ReadOnlyCachedModel):
    """
    Read/Write cached model
    """

    timeout: ClassVar[Optional[int]] = None

    @classmethod
    def _get_matched_keys(cls, data: dict) -> List[str]:
        pattern = cls.ns
        for _field in cls.key_fields:
            pattern += f':{data.get(_field, "*")}'
        return cls.connection.keys(pattern)  # type: ignore

    @classmethod
    def create(cls, **data: Any):
        key = cls.prefix_key(data)
        cls.connection.set(key, json.dumps(data))
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def create_lookup(cls, **data: Any):
        key = cls.prefix_key(data)
        cls.connection.set(key, 1)
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def create_counter(cls, starting=1, **data: Any):
        key = cls.prefix_key(data)
        cls.connection.set(key, starting)
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def update(cls, **data):
        # key = cls.prefix_key(data)
        # NOTE: keepttl works only with Redis 6.0+
        # cls.connection.set(key, json.dumps(data), keepttl=True)
        cls.create(**data)

    @classmethod
    def increment(cls, amount=1, **data):
        key = cls.prefix_key(data)
        cls.connection.incr(key, amount)

    @classmethod
    def decrement(cls, amount=1, **data):
        key = cls.prefix_key(data)
        cls.connection.decr(key, amount)

    @classmethod
    def delete(cls, **data):
        key = cls.prefix_key(data)
        cls.connection.delete(key)

    @classmethod
    def delete_all(cls, **data):
        keys = cls._get_matched_keys(data)
        if keys:
            cls.connection.delete(*keys)
