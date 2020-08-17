import json


class ReadOnlyCachedModel:
    '''
    Read only cached model
    '''
    connection = None
    key_prefix = None
    key_fields = None

    @classmethod
    def _generate_key(cls, data):
        key = cls.key_prefix
        for field in cls.key_fields:
            key += f':{data[field]}'
        return key

    @classmethod
    def get(cls, **data):
        key = cls._generate_key(data)
        value = cls.connection.get(key)
        return json.loads(value) if value else None

    @classmethod
    def exists(cls, **data):
        key = cls._generate_key(data)
        return cls.connection.exists(key)


class ReadWriteCachedModel(ReadOnlyCachedModel):
    '''
    Read/Write cached model
    '''
    timeout = None

    @classmethod
    def _get_matched_keys(cls, data):
        pattern = cls.key_prefix
        for field in cls.key_fields:
            pattern += f':{data.get(field, "*")}'
        return cls.connection.keys(pattern)

    @classmethod
    def create(cls, **data):
        key = cls._generate_key(data)
        cls.connection.set(key, json.dumps(data))
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def create_lookup(cls, **data):
        key = cls._generate_key(data)
        cls.connection.set(key, 1)
        if cls.timeout:
            cls.connection.expire(key, cls.timeout)

    @classmethod
    def delete(cls, **data):
        key = cls._generate_key(data)
        cls.connection.delete(key)

    @classmethod
    def delete_all(cls, **data):
        keys = cls._get_matched_keys(data)
        if keys:
            cls.connection.delete(*keys)
