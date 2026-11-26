import pytest
from redis import Redis

from converge import settings
from apphelpers.utilities.caching import ReadWriteCachedHashModel, ReadWriteCachedModel


class Product(ReadWriteCachedModel):
    ns = "test_cache_product"
    key_fields = ["id"]
    secondary_key_fields = ["sku"]
    timeout = 30


class ProductHash(ReadWriteCachedHashModel):
    ns = "test_cache_product_hash"
    key_fields = ["id"]
    secondary_key_fields = []


@pytest.fixture
def redis_connection():
    connection = Redis(
        host=settings.SESSIONSDB_HOST,
        port=settings.SESSIONSDB_PORT,
        password=settings.SESSIONSDB_PASSWD,
        db=settings.SESSIONSDB_NO,
        decode_responses=True,
    )
    connection.ping()
    keys = connection.keys("test_cache_product*")
    if keys:
        connection.delete(*keys)
    Product.connection = connection
    ProductHash.connection = connection

    yield connection

    keys = connection.keys("test_cache_product*")
    if keys:
        connection.delete(*keys)
    connection.close()


def test_key_patterns_and_json_values(redis_connection):
    assert Product._prefix_key({"id": 7}) == "test_cache_product:7"
    assert Product._generate_key_pattern({"id": 7}) == "test_cache_product:7"
    assert Product._generate_key_pattern({}) == "test_cache_product:*"
    assert Product._secondary_prefix_key({"sku": "A"}) == "test_cache_product:_sk_:A"

    assert Product.create(id=7, name="phone") == "test_cache_product:7"
    assert Product.get(id=7) == {"id": 7, "name": "phone"}
    assert Product.get(id=8) is None


def test_secondary_key_lookup(redis_connection):
    assert Product.create(id=7, name="phone") == "test_cache_product:7"
    assert Product.add_secondary_key("test_cache_product:7", sku="A")
    assert Product.get_by_secondary_key(sku="A") == {"id": 7, "name": "phone"}
    assert Product.get_by_secondary_key(sku="missing") is None


def test_exists_count_expiry_and_matched_keys(redis_connection):
    Product.create_counter(starting=3, id=1)
    Product.create(id=2, name="tablet")

    assert Product.exists(id=1)
    assert not Product.exists(id=99)
    assert Product.get_count(id=1) == 3
    assert Product.get_count(id=99) == 0
    count, expiry = Product.get_count_with_expiry(id=1)
    assert count == 3
    assert expiry > 0
    assert Product.count_matched_keys(in_batches=False) == 2
    assert Product.count_matched_keys(in_batches=True) == 2


def test_create_update_lookup_and_counter(redis_connection):
    assert Product.create(id=1, name="phone") == "test_cache_product:1"
    assert Product.get(id=1) == {"id": 1, "name": "phone"}

    Product.update(id=1, name="tablet")
    assert Product.get(id=1) == {"id": 1, "name": "tablet"}

    assert Product.create_lookup(id=2) == "test_cache_product:2"
    assert redis_connection.get("test_cache_product:2") == "1"
    assert Product.create_counter(starting=5, id=3) == "test_cache_product:3"
    assert redis_connection.get("test_cache_product:3") == "5"


def test_secondary_key_create_and_delete(redis_connection):
    assert Product.add_secondary_key("test_cache_product:7", sku="A")
    assert redis_connection.get("test_cache_product:_sk_:A") == "test_cache_product:7"
    Product.delete_secondary_key(sku="A")
    assert redis_connection.get("test_cache_product:_sk_:A") is None


def test_increment_decrement_and_delete(redis_connection):
    Product.create_counter(starting=10, id=1)
    Product.increment(amount=4, id=1)
    assert Product.get_count(id=1) == 14
    Product.decrement(amount=3, id=1)
    assert Product.get_count(id=1) == 11
    Product.delete(id=1)
    assert not Product.exists(id=1)


def test_delete_all_modes(redis_connection):
    Product.create(id=1, name="phone")
    Product.create(id=2, name="tablet")

    Product.delete_all(in_batches=False)
    assert not Product.exists(id=1)
    assert not Product.exists(id=2)

    Product.create(id=3, name="watch")
    Product.delete_all(in_batches=True)
    assert not Product.exists(id=3)


def test_delete_all_secondary_keys(redis_connection):
    Product.add_secondary_key("test_cache_product:1", sku="A")
    Product.add_secondary_key("test_cache_product:2", sku="B")
    Product.create(id=1, name="phone")

    Product.delete_all_secondary_keys()
    assert redis_connection.keys("test_cache_product:_sk_:*") == []
    assert Product.exists(id=1)


def test_hash_add_get_remove_and_bulk_operations(redis_connection):
    ProductHash.add("name", "phone", id=1)
    assert ProductHash.get("name", id=1) == "phone"

    ProductHash.bulk_add({"brand": "Acme", "color": "blue"}, id=1)
    assert ProductHash.bulk_get(["name", "brand", "missing"], id=1) == [
        "phone",
        "Acme",
        None,
    ]
    assert ProductHash.bulk_get([], id=1) == []
    assert ProductHash.get_all(id=1) == {
        "name": "phone",
        "brand": "Acme",
        "color": "blue",
    }

    ProductHash.remove("name", id=1)
    assert ProductHash.get("name", id=1) is None
    ProductHash.bulk_remove(["brand", "color"], id=1)
    assert ProductHash.get_all(id=1) == {}
