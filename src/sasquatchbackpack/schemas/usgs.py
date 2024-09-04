"""USGS Schemas."""

from dataclasses import dataclass, field

from dataclasses_avroschema import AvroModel


@dataclass
class EarthquakeSchema(AvroModel):
    """USGS Earthquake schema."""

    timestamp: int
    id: str = field(metadata={"description": "unique earthquake id"})
    latitude: float = field(metadata={"units": "degree"})
    longitude: float = field(metadata={"units": "degree"})
    depth: float = field(metadata={"units": "km"})
    magnitude: float = field(metadata={"units": "u.richter_magnitudes"})

    class Meta:
        """Schema metadata."""

        namespace = "$namespace"
        name = "$topic_name"
        description = "Collection of earthquakes near the summit"
