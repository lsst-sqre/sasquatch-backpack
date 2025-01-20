"""Accesses the USGSLibcomcat API."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from libcomcat.search import search

from sasquatchbackpack.sasquatch import DataSource
from sasquatchbackpack.schemas.usgs import EarthquakeSchema

__all__ = ["USGSConfig", "USGSSource"]


def search_api(
    duration: timedelta,
    radius: int = 400,
    coords: tuple[float, float] = (-30.22573200864174, -70.73932987127506),
    magnitude_bounds: tuple[int, int] = (2, 10),
) -> list:
    """Seaches USGS databases for relevant earthquake data.

    Parameters
    ----------
        duration (datetime.timedelta): How far back from the present
            should be searched.
        radius (int, optional): radius of search from central
            coordinates in km. Defaults to 400km.
        coords (tuple(float,float), optional): latitude and longitude of
            the central coordnates. Latitude is first and Longitude is
            second. Defaults to the latitude and longitude of Cerro
            Pachon.
        min_magnitude (int, optional): minimum earthquake magnitude.
            Defaults to 2.
        max_magnitude (int, optional): maximum earthquake magnitude.
            Defaults to 10.
    """
    # Linting bypassed, as at the time of writing Libcomcat breaks if provided
    # with a timezone-aware datetime object
    current_dt = datetime.utcnow()  # noqa: DTZ003

    return search(
        starttime=current_dt - duration,
        endtime=current_dt,
        maxradiuskm=radius,
        latitude=coords[0],
        longitude=coords[1],
        minmagnitude=magnitude_bounds[0],
        maxmagnitude=magnitude_bounds[1],
    )


@dataclass
class USGSConfig:
    """Class containing relevant configuration information for the
    USGSSource.

    Parameters
    ----------
    duration : datetime.timedelta
        How far back from the present should be searched
    radius : int
        Radius of search from central coordinates in km
    coords : tuple[float,float]
        Latitude and longitude of the central coordnates
        (latitude, longitude)
    magnitude_bounds : tuple[int, int]
        Upper and lower bounds for magnitude search (lower, upper)
    topic_name : `str`, optional
        Name of the the sasquatch topic
    """

    duration: timedelta
    radius: int
    coords: tuple[float, float]
    magnitude_bounds: tuple[int, int]
    topic_name: str = "usgs_earthquake_data"


class USGSSource(DataSource):
    """Backpack data source for the USGS Earthquake API.

    Parameters
    ----------
    config : USGSConfig
        USGSConfig to transmit relevant information to
        the Source
    """

    def __init__(
        self,
        config: USGSConfig,
    ) -> None:
        super().__init__(config.topic_name)
        self.duration = config.duration
        self.config = config
        self.schema = EarthquakeSchema.avro_schema().replace("double", "float")
        self.radius = config.radius
        self.coords = config.coords
        self.magnitude_bounds = config.magnitude_bounds

    def load_schema(self) -> str:
        """Load the relevant schema."""
        return self.schema

    def get_records(self) -> list[dict]:
        """Call the USGS Comcat API and assembles records.

        Returns
        -------
        List[dict] : list[dict]
            A payload consisting of a list of dictionaries,
            each containing data about a specific earthquake
            in the build results.
        """
        try:
            results = search_api(
                self.duration,
                self.radius,
                self.coords,
                self.magnitude_bounds,
            )

            return [
                {
                    "value": {
                        "timestamp": int(result.time.strftime("%s")),
                        "id": result.id,
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "depth": float(result.depth),
                        "magnitude": float(result.magnitude),
                    }
                }
                for result in results
            ]
        except ConnectionError as ce:
            raise ConnectionError(
                f"A connection error occurred while fetching records: {ce}"
            ) from ce

    def get_redis_key(self, datapoint: dict) -> str:
        """Allow USGS API to format its own redis keys.
        For usage in the BackpackDispatcher.

        Parameters
        ----------
        datapoint : dict
            An individual result from the list output of get_records().

        Returns
        -------
        str : str
            A deterministic redis key for this specific data point.
        """
        # Redis keys are formatted "topic_name:key_value"
        # to keep data from different APIs discreet
        return f"{self.topic_name}:{datapoint['value']['id']}"
