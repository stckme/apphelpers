import pytest
import pytest_asyncio
from redis.asyncio import Redis

from converge import settings
from apphelpers.utilities.async_caching import ReadWriteAsyncCachedModel
from apphelpers.utilities.async_caching import ReadWriteCachedHashAsyncModel


class Product(ReadWriteAsyncCachedModel):
    ns = "test_async_cache_product"
    key_fields = ["id"]
    secondary_key_fields = ["sku"]
    timeout = 30


class ProductHash(ReadWriteCachedHashAsyncModel):
    ns = "test_async_cache_product_hash"
    key_fields = ["id"]
    secondary_key_fields = []


@pytest_asyncio.fixture
async def redis_connection():
    connection = Redis(
        host=settings.SESSIONSDB_HOST,
        port=settings.SESSIONSDB_PORT,
        password=settings.SESSIONSDB_PASSWD,
        db=settings.SESSIONSDB_NO,
        decode_responses=True,
    )
    await connection.ping()
    keys = await connection.keys("test_async_cache_product*")
    if keys:
        await connection.delete(*keys)
    Product.connection = connection
    ProductHash.connection = connection

    yield connection

    keys = await connection.keys("test_async_cache_product*")
    if keys:
        await connection.delete(*keys)
    await connection.aclose()


@pytest.mark.asyncio
async def test_async_key_patterns_and_json_values(redis_connection):
    assert Product._prefix_key({"id": 7}) == "test_async_cache_product:7"
    assert Product._generate_key_pattern({"id": 7}) == "test_async_cache_product:7"
    assert Product._generate_key_pattern({}) == "test_async_cache_product:*"
    assert (
        Product._secondary_prefix_key({"sku": "A"}) == "test_async_cache_product:_sk_:A"
    )

    assert await Product.create(id=7, name="phone") == "test_async_cache_product:7"
    assert await Product.get(id=7) == {"id": 7, "name": "phone"}
    assert await Product.get(id=8) is None


@pytest.mark.asyncio
async def test_async_secondary_key_lookup(redis_connection):
    await Product.create(id=7, name="phone")
    await Product.add_secondary_key("test_async_cache_product:7", sku="A")
    assert await Product.get_by_secondary_key(sku="A") == {"id": 7, "name": "phone"}
    assert await Product.get_by_secondary_key(sku="missing") is None


@pytest.mark.asyncio
async def test_async_exists_count_expiry_and_matched_keys(redis_connection):
    await Product.create_counter(starting=3, id=1)
    await Product.create(id=2, name="tablet")

    assert await Product.exists(id=1)
    assert not await Product.exists(id=99)
    assert await Product.get_count(id=1) == 3
    assert await Product.get_count(id=99) == 0
    count, expiry = await Product.get_count_with_expiry(id=1)
    assert count == 3
    assert expiry > 0
    assert await Product.count_matched_keys(in_batches=False) == 2
    assert await Product.count_matched_keys(in_batches=True, batch_size=1) == 2


@pytest.mark.asyncio
async def test_async_create_update_lookup_and_counter(redis_connection):
    assert await Product.create(id=1, name="phone") == "test_async_cache_product:1"
    assert await Product.get(id=1) == {"id": 1, "name": "phone"}

    await Product.update(id=1, name="tablet")
    assert await Product.get(id=1) == {"id": 1, "name": "tablet"}

    assert await Product.create_lookup(id=2) == "test_async_cache_product:2"
    assert await redis_connection.get("test_async_cache_product:2") == "1"
    assert (
        await Product.create_counter(starting=5, id=3) == "test_async_cache_product:3"
    )
    assert await redis_connection.get("test_async_cache_product:3") == "5"


@pytest.mark.asyncio
async def test_async_secondary_key_create_and_delete(redis_connection):
    await Product.add_secondary_key("test_async_cache_product:7", sku="A")
    assert (
        await redis_connection.get("test_async_cache_product:_sk_:A")
        == "test_async_cache_product:7"
    )
    await Product.delete_secondary_key(sku="A")
    assert await redis_connection.get("test_async_cache_product:_sk_:A") is None


@pytest.mark.asyncio
async def test_async_increment_decrement_and_delete(redis_connection):
    await Product.create_counter(starting=10, id=1)
    await Product.increment(amount=4, id=1)
    assert await Product.get_count(id=1) == 14
    await Product.decrement(amount=3, id=1)
    assert await Product.get_count(id=1) == 11
    await Product.delete(id=1)
    assert not await Product.exists(id=1)


@pytest.mark.asyncio
async def test_async_delete_all_modes(redis_connection):
    await Product.create(id=1, name="phone")
    await Product.create(id=2, name="tablet")

    await Product.delete_all(in_batches=False)
    assert not await Product.exists(id=1)
    assert not await Product.exists(id=2)

    await Product.create(id=3, name="watch")
    await Product.delete_all(in_batches=True, batch_size=1)
    assert not await Product.exists(id=3)


@pytest.mark.asyncio
async def test_async_delete_all_secondary_keys(redis_connection):
    await Product.add_secondary_key("test_async_cache_product:1", sku="A")
    await Product.add_secondary_key("test_async_cache_product:2", sku="B")
    await Product.create(id=1, name="phone")

    await Product.delete_all_secondary_keys()
    assert await redis_connection.keys("test_async_cache_product:_sk_:*") == []
    assert await Product.exists(id=1)


@pytest.mark.asyncio
async def test_async_hash_add_get_remove_and_bulk_operations(redis_connection):
    await ProductHash.add("name", "phone", id=1)
    assert await ProductHash.get("name", id=1) == "phone"

    await ProductHash.bulk_add({"brand": "Acme", "color": "blue"}, id=1)
    assert await ProductHash.bulk_get(["name", "brand", "missing"], id=1) == [
        "phone",
        "Acme",
        None,
    ]
    assert await ProductHash.bulk_get([], id=1) == []
    assert await ProductHash.get_all(id=1) == {
        "name": "phone",
        "brand": "Acme",
        "color": "blue",
    }

    await ProductHash.remove("name", id=1)
    assert await ProductHash.get("name", id=1) is None
    await ProductHash.bulk_remove(["brand", "color"], id=1)
    assert await ProductHash.get_all(id=1) == {}
