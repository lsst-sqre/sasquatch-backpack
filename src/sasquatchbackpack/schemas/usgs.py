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
        self.model = None
        self.address = address

    def start_redis(self) -> None:
        redis_client = redis.Redis.from_url(self.address)
        self.model = PydanticRedisStorage(
            datatype=EarthquakeSchema, redis=redis_client
        )

    async def store(self, key: str, item: EarthquakeSchema) -> None:
        if self.model is None:
            return

        await self.model.store(key, item)

    async def get(self, key: str) -> EarthquakeSchema:
        return await self.model.get(key)
