from datetime import timedelta

from sasquatchbackpack.scripts import usgs


class data_source:
    """Base class for all relevant backpack data sources

    Parameters
    ----------
    namespace
        Which kafka namespace should be used, see
        https://sasquatch.lsst.io/user-guide/namespaces.html#namespaces
    topic name
        Specific source name, used as an identifier
    schema directory
        Directory path to the relevant source schema, eg:
         "src/sasquatchbackpack/schemas/*.avsc"
    """

    def __init__(self, namespace: str, topic_name: str, schema_directory: str):
        self.namespace = namespace
        self.topic_name = topic_name
        self.schema_directory = schema_directory
        self.results = []

    def set_new_payload_values(self):
        """Template method that should allow alteration of provided
        parameters then rebuild results
        """
        pass

    def build_results(self):
        """Template method that should create a dataset based off the
        current provided parameters and update results.
        """
        pass

    def get_records(self):
        """Template method that should assemble a payload based off
        built results
        """
        pass

    def get_results(self) -> list:
        """Gives access to most recent result list

        Returns
        -------
        results
            Most recent list of results built with build_results()
        """
        return self.results

    def get_schema_directory(self) -> str:
        """Gives access to the provided schema directory path

        Returns
        -------
        schema directory
            Provided path to the relevant source's schema
        """
        return self.schema_directory


class usgs_source(data_source):
    """Backpack data source for the USGS Earthquake API

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
    namespace
        Which kafka namespace should be used, see
        https://sasquatch.lsst.io/user-guide/namespaces.html#namespaces
        , optional, defaults to "lsst.example"
    topic name
        Specific source name, used as an identifier, optional,
        defaults to "usgs-earthquake-data"
    schema directory
        Directory path to the relevant source schema
        ("src/sasquatchbackpack/schemas/*.avsc"), optional,
        defaults to "src/sasquatchbackpack/schemas/usgs.avsc"
    """

    def __init__(
        self,
        duration: timedelta,
        radius: int,
        coords: tuple[float, float],
        magnitude_bounds: tuple[int, int],
        namespace: str = "lsst.example",
        topic_name: str = "usgs-earthquake-data",
        schema_directory: str = "src/sasquatchbackpack/schemas" + "/usgs.avsc",
    ):
        super().__init__(namespace, topic_name, schema_directory)
        self.duration = duration
        self.radius = radius
        self.coords = coords
        self.magnitude_bounds = magnitude_bounds
        self.build_results()

    def set_new_payload_values(
        self,
        new_duration: timedelta = None,
        new_radius: int = None,
        new_coords: tuple[float, float] = None,
        new_magnitude_bounds: tuple[int, int] = None,
    ):
        """Alters payload values then rebuilds results using new values

        Parameters
        ----------
        duration
            How far back from the present should be searched, optional
        radius
            Padius of search from central coordinates in km, optional
        coords
            latitude and longitude of the central coordnates
            (latitude, longitude), optional
        magnitude bounds
            upper and lower bounds for magnitude search
            (lower, upper), optional
        """
        if new_duration is not None:
            self.duration = new_duration
        if new_radius is not None:
            self.radius = new_radius
        if new_coords is not None:
            self.coords = new_coords
        if new_magnitude_bounds is not None:
            self.magnitude_bounds = new_magnitude_bounds

        self.build_results()

    def build_results(self):
        """Query the USGS API using the current provided parameters,
        then update results.
        """
        self.results = usgs.search_api(
            self.duration,
            self.radius,
            self.coords,
            self.magnitude_bounds,
        )

    def get_records(self) -> list:
        """Assembles a payload based off most recent build results

        Returns
        -------
        records
            A payload consisting of a list of dictionaries,
            each containing data about a specific earthquake
            in the build results.
        """
        records = []

        for result in self.results:
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
