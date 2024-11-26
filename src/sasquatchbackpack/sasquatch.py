"""Handles dispatch of backpack data to kafka."""

__all__ = ["BackpackDispatcher", "DispatcherConfig", "DataSource"]

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from string import Template

import requests

from sasquatchbackpack.schemas import usgs as schemas

# Code yoinked from https://github.com/lsst-sqre/
# sasquatch/blob/main/examples/RestProxyAPIExample.ipynb

# ruff: noqa:TD002
# ruff: noqa:TD003


class DataSource(ABC):
    """Base class for all relevant backpack data sources.

    Parameters
    ----------
    topic_name : str
        Specific source name, used as an identifier
    """

    def __init__(self, topic_name: str) -> None:
        self.topic_name = topic_name

    @abstractmethod
    def load_schema(self) -> str:
        pass

    @abstractmethod
    def get_records(self) -> list[dict]:
        pass

    @abstractmethod
    def get_redis_key(self, datapoint: dict) -> str:
        pass


@dataclass
class DispatcherConfig:
    """Class containing relevant configuration information for the
    BackpackDispatcher.
    """

    sasquatch_rest_proxy_url: str = field(
        default=os.getenv(
            "SASQUATCH_REST_PROXY_URL",
            "https://data-int.lsst.cloud/sasquatch-rest-proxy",
        )
    )
    """Environment variable contatining the target for data"""
    partitions_count: int = 1
    """Number of topic partitions to create"""
    replication_factor: int = 3
    """Number of topic replicas to create"""
    namespace: str = field(
        default=os.getenv("BACKPACK_NAMESPACE", "lsst.backpack")
    )
    """Sasquatch namespace for the topic"""
    redis_address: str = "redis://localhost:6379/0"
    """Address of Redis server"""


class BackpackDispatcher:
    """A class to send backpack data to kafka.

    Parameters
    ----------
    source : DataSource
        DataSource containing schema and record data to be
        posted to remote
    config : DispatcherConfig
        Item that transmits other relevant information to
        the Dispatcher
    """

    def __init__(self, source: DataSource, config: DispatcherConfig) -> None:
        self.source = source
        self.config = config
        self.schema = Template(source.load_schema()).substitute(
            {
                "namespace": self.config.namespace,
                "topic_name": self.source.topic_name,
            }
        )
        self.redis = schemas.EarthquakeRedisManager(config.redis_address)

    def create_topic(self) -> str:
        """Create kafka topic based off data from provided source.

        Returns
        -------
        response text : str
            The results of the requests in string format
        """
        headers = {"content-type": "application/json"}

        try:
            r = requests.get(
                f"{self.config.sasquatch_rest_proxy_url}/v3/clusters",
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()  # Raises HTTPError for bad responses
            cluster_id = r.json()["data"][0]["cluster_id"]
        except requests.RequestException as e:
            return f"Error getting cluster ID: {e}"

        topic_config = {
            "topic_name": f"{self.config.namespace}."
            f"{self.source.topic_name}",
            "partitions_count": self.config.partitions_count,
            "replication_factor": self.config.replication_factor,
        }

        headers = {"content-type": "application/json"}

        try:
            response = requests.post(
                f"{self.config.sasquatch_rest_proxy_url}/v3/clusters/"
                f"{cluster_id}/topics",
                json=topic_config,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()  # Raises HTTPError for bad responses
        except requests.RequestException as e:
            return f"Error POSTing data: {e}"

        return response.text

    def _remove_redis_duplicates(self, records: list[dict]) -> list[dict]:
        """Check the redis server for any duplicate data points
        present in the provided records, and return a list with them removed.

        Parameters
        ----------
        records : list[dict]
            Output of a source.get_records() call.

        Returns
        -------
        final : list[dict]
            List with duplicate elements in common with those
            on the redis server removed.
        """
        final = []

        for record in records:
            if self.redis.get(self.source.get_redis_key(record)) is None:
                final.append(record)  # noqa: PERF401

        return final

    def post(self) -> str:
        """Assemble schema and payload from the given source, then
        makes a POST request to kafka.

        Returns
        -------
        response text : str
            The results of the POST request in string format
        """
        records = self._remove_redis_duplicates(self.source.get_records())

        payload = {"value_schema": self.schema, "records": records}

        url = (
            f"{self.config.sasquatch_rest_proxy_url}/topics/"
            f"{self.config.namespace}.{self.source.topic_name}"
        )

        headers = {
            "Content-Type": "application/vnd.kafka.avro.v2+json",
            "Accept": "application/vnd.kafka.v2+json",
        }

        try:
            response = requests.request(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()  # Raises HTTPError for bad responses
        except requests.RequestException as e:
            return f"Error POSTing data: {e}"

        for record in records:
            self.redis.store(
                self.source.get_redis_key(record),
                schemas.EarthquakeSchema(
                    timestamp=0,
                    id="",
                    latitude=0,
                    longitude=0,
                    depth=0,
                    magnitude=0,
                ),
            )

        return response.text
