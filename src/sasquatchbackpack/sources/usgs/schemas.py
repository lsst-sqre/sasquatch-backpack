"""USGS Schemas."""

from dataclasses_avroschema.pydantic import AvroBaseModel
from pydantic import BaseModel, Field


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

        namespace = "Default"
        schema_name = "usgsEarthquakeData"


class EarthquakeRequest(BaseModel):
    """Request body for USGS API earthquake query parameters."""

    days: int = Field(
        description="The number of days to look "
        "back from the present when performing the search."
    )
    hours: int = Field(
        description="The number of hours to look "
        "back from the present when performing the search."
    )

    radius: int = Field(
        default=400,
        description="The radius around the provided coordinate to search.",
    )

    latitude: float = Field(
        default=-30.22573200864174,
        description="The latitude of the center coordinate",
    )

    longitude: float = Field(
        default=-70.73932987127506,
        description="The longitude of the center coordinate",
    )

    lower: int = Field(
        default=2,
        description="The lower bound for earthquake magnitude to search",
    )

    upper: int = Field(
        default=10,
        description="The upper bound for earthquake magnitude to search",
    )

    publish: bool = Field(
        default=False,
        description="Whether or not queried data should be published to"
        "sasquatch",
    )

    method: str = Field(
        default="DIRECT_CONNECTION",
        description="The publish method for sending data to sasquatch",
    )
