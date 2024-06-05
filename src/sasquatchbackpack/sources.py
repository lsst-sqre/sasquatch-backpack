"""Framework and implementation for data structures to post data to kafka."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from sasquatchbackpack.scripts import usgs


class DataSource(ABC):
    """Base class for all relevant backpack data sources.

    Parameters
    ----------
    topic name
        Specific source name, used as an identifier
    """

    def __init__(self, topic_name: str) -> None:
        self.topic_name = topic_name

    @abstractmethod
    def load_schema(self) -> str:
        pass

    @abstractmethod
    def get_records(self) -> list:
        pass


@dataclass
class USGSConfig:
    """Class containing relevant configuration information for the
    USGSSource.

    Parameters
    ----------
    duration
        How far back from the present should be searched
    radius
        Padius of search from central coordinates in km
    coords
        latitude and longitude of the central coordnates
        (latitude, longitude)
    magnitude bounds
        upper and lower bounds for magnitude search (lower, upper)
    schema file
        Directory path to the relevant source schema
        ("src/sasquatchbackpack/schemas/*.avsc"), optional,
        defaults to "src/sasquatchbackpack/schemas/usgs.avsc"
    """

    duration: timedelta
    radius: int
    coords: tuple[float, float]
    magnitude_bounds: tuple[int, int]
    schema_file: str = "src/sasquatchbackpack/schemas/usgs.avsc"


class USGSSource(DataSource):
    """Backpack data source for the USGS Earthquake API.

    Parameters
    ----------
    config
        USGSConfig to transmit relevant information to
        the Source
    topic name
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
        with Path(self.config.schema_file).open("r") as file:
            return file.read()

    def get_records(self) -> list:
        """Call the USGS Comcat API and assembles records.

        Returns
        -------
        records
            A payload consisting of a list of dictionaries,
            each containing data about a specific earthquake
            in the build results.
        """
        results = usgs.search_api(
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
