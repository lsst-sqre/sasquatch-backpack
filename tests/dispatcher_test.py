"""Test the Sasquatch Dispatcher."""

import os

from dataclasses_avroschema.pydantic import AvroBaseModel
from pydantic import Field

from sasquatchbackpack import sasquatch


class TestSchema(AvroBaseModel):
    """Schema for testing."""

    id: str = Field(description="event id")

    class Meta:
        """Schema metadata."""

        namespace = "$namespace"
        schema_name = "$topic_name"


class TestSource(sasquatch.DataSource):
    def __init__(self, current_records: list[dict[str, str]]) -> None:
        super().__init__(
            "test",
            TestSchema.avro_schema().replace("double", "float"),
            uses_redis=True,
        )
        self.records = current_records

    def get_records(self) -> list[dict]:
        return [{"value": {"id": record["id"]}} for record in self.records]

    def get_redis_key(self, datapoint: dict) -> str:
        return f"{self.topic_name}:{datapoint['value']['id']}"


def test_get_source_records() -> None:
    source = TestSource([{"id": "abc123"}, {"id": "123abc"}])
    dispatcher = sasquatch.BackpackDispatcher(
        source, "redis://localhost:" + os.environ["REDIS_6379_TCP_PORT"] + "/0"
    )
    dispatcher.redis.store("test:abc123")

    # Ensure item was successfully added
    result = dispatcher.redis.get("test:abc123")
    assert result is not None

    assert dispatcher._get_source_records() == [{"value": {"id": "123abc"}}]


# Add test for uses_redis == False
