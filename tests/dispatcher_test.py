"""Test the Sasquatch Dispatcher."""

import os

import pytest
from dataclasses_avroschema.pydantic import AvroBaseModel
from faststream.kafka import KafkaBroker
from pydantic import Field
from safir.kafka import PydanticSchemaManager

from sasquatchbackpack import sasquatch


class TestSchema(AvroBaseModel):
    """Schema for testing."""

    id: str = Field(description="event id")

    class Meta:
        """Schema metadata."""

        namespace = "Default"
        schema_name = "testSchema"


class TestSource(sasquatch.DataSource):
    def __init__(
        self, current_records: list[dict[str, str]], *, redis: bool = True
    ) -> None:
        super().__init__(
            "test",
            uses_redis=redis,
        )
        self.records = current_records

    def assemble_schema(
        self, namespace: str, records: dict | None = None
    ) -> AvroBaseModel:
        if records is None:
            schema = {
                "id": "default",
                "namespace": namespace,
            }
        else:
            record_val: dict = records["value"]
            schema = {
                "id": record_val["id"],
                "namespace": namespace,
            }
        return TestSchema.parse_obj(data=schema)

    def get_records(self) -> list[dict]:
        return [{"value": {"id": record["id"]}} for record in self.records]

    def get_redis_key(self, datapoint: dict) -> str:
        return f"{self.topic_name}:{datapoint['value']['id']}"


@pytest.mark.skip(reason="temporary breakage")
def test_get_source_records(
    kafka_broker: KafkaBroker, schema_manager: PydanticSchemaManager
) -> None:
    source = TestSource([{"id": "abc123"}, {"id": "123abc"}])
    dispatcher = sasquatch.BackpackDispatcher(
        source,
        "redis://localhost:" + os.environ["REDIS_6379_TCP_PORT"] + "/0",
        kafka_broker,
        schema_manager,
    )

    assert dispatcher._get_source_records() == [
        {
            "value": {
                "id": "abc123",
            },
        },
        {
            "value": {
                "id": "123abc",
            },
        },
    ]


@pytest.mark.skip(reason="temporary breakage")
def test_publish(
    kafka_broker: KafkaBroker, schema_manager: PydanticSchemaManager
) -> None:
    source = TestSource([{"id": "abc321"}])
    dispatcher = sasquatch.BackpackDispatcher(
        source,
        "redis://localhost:" + os.environ["REDIS_6379_TCP_PORT"] + "/0",
        kafka_broker,
        schema_manager,
    )
    result = dispatcher.publish()
    # Ensure clean run
    assert "Error" not in result[0]

    # Ensure item was successfully added to redis
    redis = dispatcher.redis.get("test:abc321")
    assert redis is not None


@pytest.mark.skip(reason="temporary breakage")
def test_redis_off(
    kafka_broker: KafkaBroker, schema_manager: PydanticSchemaManager
) -> None:
    source = TestSource([{"id": "cba321"}], redis=False)
    dispatcher = sasquatch.BackpackDispatcher(
        source,
        "redis://localhost:" + os.environ["REDIS_6379_TCP_PORT"] + "/0",
        kafka_broker,
        schema_manager,
    )
    result = dispatcher.publish()

    # Ensure clean run
    assert "Error" not in result[0]

    # Ensure item was not added to redis
    redis = dispatcher.redis.get("test:cba321")
    assert redis is None
