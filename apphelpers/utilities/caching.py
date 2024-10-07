from __future__ import annotations

import json
from typing import Any, ClassVar, List, Optional

from redis import Redis


class ReadOnlyCachedModel:
    """
    Read only cached model
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
    def _get_matched_keys(cls, data: dict) -> List[str]:
        pattern = cls.ns
        for _field in cls.key_fields:
            pattern += f':{data.get(_field, "*")}'
        return cls.connection.keys(pattern)  # type: ignore

    @classmethod
    def get(cls, **data: Any) -> Optional[dict]:
        key = cls._prefix_key(data)
        value: Any = cls.connection.get(key)
        return json.loads(value) if value else None

    @classmethod
    def get_by_secondary_key(cls, **data: Any) -> Optional[dict]:
        secondary_key = cls._secondary_prefix_key(data)
        primary_key = cls.connection.get(secondary_key)
        if primary_key:
            value = cls.connection.get(primary_key)
            return json.loads(value) if value else None

    @classmethod
    def exists(cls, **data: Any) -> bool:
        key = cls._prefix_key(data)
        return cls.connection.exists(key)  # type: ignore

    @classmethod
    def get_count(cls, **data: Any) -> int:
        key: Any = cls._prefix_key(data)
        count: Optional[Any] = cls.connection.get(key)
        return int(count) if count else 0

    @classmethod
    def count_matched_keys(cls, **data: Any) -> int:
        keys = cls._get_matched_keys(data)
        return len(keys)


class ReadWriteCachedModel(ReadOnlyCachedModel):
    """
    Read/Write cached model
    """

    timeout: ClassVar[Optional[int]] = None

    @classmethod
    def create(cls, **data: Any) -> str:
        key = cls._prefix_key(data)
        cls.connection.set(key, json.dumps(data))
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)
        return key

    @classmethod
    def add_secondary_key(cls, primary_key: str, **data: Any) -> str:
        secondary_key = cls._secondary_prefix_key(data)
        cls.connection.set(secondary_key, primary_key)
        return secondary_key

    @classmethod
    def create_lookup(cls, **data: Any) -> str:
        key = cls._prefix_key(data)
        cls.connection.set(key, 1)
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)
        return key

    @classmethod
    def create_counter(cls, starting=1, **data: Any) -> str:
        key = cls._prefix_key(data)
        cls.connection.set(key, starting)
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)
        return key

    @classmethod
    def update(cls, **data):
        # key = cls._prefix_key(data)
        # NOTE: keepttl works only with Redis 6.0+
        # cls.connection.set(key, json.dumps(data), keepttl=True)
        cls.create(**data)

    @classmethod
    def increment(cls, amount=1, **data):
        key = cls._prefix_key(data)
        cls.connection.incr(key, amount)

    @classmethod
    def decrement(cls, amount=1, **data):
        key = cls._prefix_key(data)
        cls.connection.decr(key, amount)

    @classmethod
    def delete(cls, **data):
        key = cls._prefix_key(data)
        cls.connection.delete(key)

    @classmethod
    def delete_secondary_key(cls, **data: Any):
        secondary_key = cls._secondary_prefix_key(data)
        cls.connection.delete(secondary_key)

    @classmethod
    def delete_all(cls, **data):
        keys = cls._get_matched_keys(data)
        if keys:
            cls.connection.delete(*keys)

    @classmethod
    def delete_all_secondary_keys(cls):
        secondary_keys = cls.connection.keys(cls._secondary_prefix_key(data={}))
        if secondary_keys:
            cls.connection.delete(*secondary_keys)
