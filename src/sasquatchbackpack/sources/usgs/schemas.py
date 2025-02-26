"""USGS Schemas."""

from dataclasses_avroschema.pydantic import AvroBaseModel
from pydantic import Field


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
