"""USGS Schemas."""

import redis.asyncio as redis
from dataclasses_avroschema.pydantic import AvroBaseModel
from pydantic import Field
from safir.redis import PydanticRedisStorage


class EarthquakeSchema(AvroBaseModel):
    """Collection of earthquakes near the summit."""

    timestamp: int
    id: str = Field(metadata={"description": "unique earthquake id"})
    latitude: float = Field(metadata={"units": "degree"})
    longitude: float = Field(metadata={"units": "degree"})
    depth: float = Field(metadata={"units": "km"})
    magnitude: float = Field(metadata={"units": "u.richter_magnitudes"})

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

    async def store(self, key: str, item: EarthquakeSchema) -> bool:
        if self.model is None:
            raise RuntimeError("Model is undefined.")
        await self.model.store(key, item)
        return True

    async def get(self, key: str) -> EarthquakeSchema:
        if self.model is None:
            raise RuntimeError("Model is undefined.")
        return await self.model.get(key)
