"""Test Redis."""

import os

import pytest

from sasquatchbackpack import sasquatch


def init_redis() -> sasquatch.RedisManager:
    return sasquatch.RedisManager(
        address="redis://localhost:" + os.environ["REDIS_6379_TCP_PORT"] + "/0"
    )


@pytest.mark.skip(reason="temporary breakage")
def test_read_write() -> None:
    redis = init_redis()
    redis.store("test:abc123")

    result = redis.get("test:abc123")

    assert result is not None
    assert redis.get("test:not-a-key") is None
