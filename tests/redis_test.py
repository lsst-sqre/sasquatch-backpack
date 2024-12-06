"""Test Redis."""

from sasquatchbackpack import sasquatch


def test_read_write() -> None:
    redis = sasquatch.RedisManager(address="redis://localhost:6379/0")

    redis.store("test:abc123")

    result = redis.get("test:abc123")

    assert result is not None
    assert redis.get("test:not-a-key") is None
