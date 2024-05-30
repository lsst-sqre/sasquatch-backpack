from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from string import Template

from sasquatchbackpack.scripts import usgs


class DataSource(ABC):
    """Base class for all relevant backpack data sources

    Parameters
    ----------
    topic name
        Specific source name, used as an identifier
    """

    def __init__(self, topic_name: str):
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
    USGSSource

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
    """Backpack data source for the USGS Earthquake API

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
        topic_name: str = "usgs-earthquake-data",
    ):
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
        with open(self.config.schema_file, "r") as file:
            template = Template(file.read())

        value_schema = template.substitute(
            {
                "topic_name": self.topic_name,
            }
        )

        return value_schema

    def get_records(self) -> list:
        """Calls the USGS Comcat API and assembles records

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

        records = []

        for result in results:
            records.append(
                {
                    "value": {
                        "timestamp": result.time.strftime("%s"),
                        "id": result.id,
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "depth": float(result.depth),
                        "magnitude": float(result.magnitude),
                    }
                }
            )

        return records
