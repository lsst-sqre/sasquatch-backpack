"""USGS Schemas."""

import asyncio

import redis.asyncio as redis
from dataclasses_avroschema.pydantic import AvroBaseModel
from pydantic import Field
from safir.redis import PydanticRedisStorage


class EarthquakeSchema(AvroBaseModel):
    """Collection of earthquakes near the summit."""

    timestamp: int
    id: str = Field(description="unique earthquake id")
    latitude: float = Field(json_schema_extra={"units": "degree"})
    longitude: float = Field(json_schema_extra={"units": "degree"})
    depth: float = Field(json_schema_extra={"units": "km"})
    magnitude: float = Field(
        json_schema_extra={"units": "u.richter_magnitudes"}
    )

    class Meta:
        """Schema metadata."""

        namespace = "$namespace"
        schema_name = "$topic_name"


class EarthquakeRedisManager:
    """Manage redis for USGS."""

    def __init__(self, address: str) -> None:
        self.address = address
        connection = redis.from_url(self.address)
        self.model = PydanticRedisStorage(
            datatype=EarthquakeSchema, redis=connection
        )
        self.loop = asyncio.new_event_loop()

    def store(self, key: str, item: EarthquakeSchema) -> None:
        if self.model is None:
            raise RuntimeError("Model is undefined.")
        self.loop.run_until_complete(self.model.store(key, item))

    def get(self, key: str) -> EarthquakeSchema:
        if self.model is None:
            raise RuntimeError("Model is undefined.")
        target = self.loop.run_until_complete(self.model.get(key))
        if target is None:
            raise LookupError(f"Entry with key of {key} could not be found")
        return target
