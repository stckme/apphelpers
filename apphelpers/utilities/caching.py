import json


class ReadOnlyCachedModel:
    """
    Read only cached model
    """

    connection = None
    ns = None
    key_fields = None

    @classmethod
    def prefix_key(cls, data):
        key = cls.ns
        for field in cls.key_fields:
            key += f":{data[field]}"
        return key

    @classmethod
    def get(cls, **data):
        key = cls.prefix_key(data)
        value = cls.connection.get(key)
        return json.loads(value) if value else None

    @classmethod
    def exists(cls, **data):
        key = cls.prefix_key(data)
        return cls.connection.exists(key)

    @classmethod
    def get_count(cls, **data):
        key = cls.prefix_key(data)
        return int(cls.connection.get(key) or 0)


class ReadWriteCachedModel(ReadOnlyCachedModel):
    """
    Read/Write cached model
    """

    timeout = None

    @classmethod
    def _get_matched_keys(cls, data):
        pattern = cls.ns
        for field in cls.key_fields:
            pattern += f':{data.get(field, "*")}'
        return cls.connection.keys(pattern)

    @classmethod
    def create(cls, **data):
        key = cls.prefix_key(data)
        cls.connection.set(key, json.dumps(data))
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def create_lookup(cls, **data):
        key = cls.prefix_key(data)
        cls.connection.set(key, 1)
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def create_counter(cls, starting=1, **data):
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
