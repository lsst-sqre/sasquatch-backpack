"""Accesses the USGSLibcomcat API."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from libcomcat.search import search

from sasquatchbackpack.sasquatch import DataSource

__all__ = ["USGSSource", "USGSConfig"]


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
    schema_file : `str`, optional
        Directory path to the relevant source schema
        (src/sasquatchbackpack/schemas/schema_name_here.avsc), optional,
        defaults to src/sasquatchbackpack/schemas/usgs.avsc
    cron_schema : `str`, optional
        Directory path to the relevant source schema from a cronjob.
    """

    duration: timedelta
    radius: int
    coords: tuple[float, float]
    magnitude_bounds: tuple[int, int]
    schema_file: str = "src/sasquatchbackpack/schemas/usgs/earthquake.avsc"
    cron_schema: str = (
        "/opt/venv/lib/python3.12/site-packages/"
        "sasquatchbackpack/schemas/usgs/earthquake.avsc"
    )


class USGSSource(DataSource):
    """Backpack data source for the USGS Earthquake API.

    Parameters
    ----------
    config : USGSConfig
        USGSConfig to transmit relevant information to
        the Source
    topic_name : str
        Specific source name, used as an identifier
    """

    def __init__(
        self,
        config: USGSConfig,
        topic_name: str = "usgs_earthquake_data",
    ) -> None:
        super().__init__(topic_name)
        self.duration = config.duration
        self.config = config
        self.radius = config.radius
        self.coords = config.coords
        self.magnitude_bounds = config.magnitude_bounds

    def load_schema(self) -> str:
        """Query the USGS API using the current provided parameters,
        then update results.
        """
        try:
            with Path(self.config.schema_file).open("r") as file:
                return file.read()
        except FileNotFoundError:
            with Path(self.config.cron_schema).open("r") as file:
                return file.read()

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
