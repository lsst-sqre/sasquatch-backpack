"""Handles dispatch of backpack data to kafka."""

__all__ = ["BackpackDispatcher", "DataSource", "DispatcherConfig"]

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from string import Template

import redis.asyncio as redis
import requests

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

    def __init__(
        self, topic_name: str, schema: str, *, uses_redis: bool
    ) -> None:
        self.topic_name = topic_name
        self.schema = schema
        self.uses_redis = uses_redis

    @abstractmethod
    def get_records(self) -> list[dict]:
        pass

    @abstractmethod
    def get_redis_key(self, datapoint: dict) -> str:
        pass


class RedisManager:
    """Manage redis operations for backpack.

    Parameters
    ----------
    address : str
        Address where redis server can be accessed.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        self.model = redis.from_url(self.address)

        self.loop = asyncio.new_event_loop()

    def store(self, key: str, item: str = "value") -> None:
        """Store a key value pair in the provided redis server.

        Parameters
        ----------
        key : str
            Key that will be used to access the stored data.
        item : str
            Value that will be stored. Defaults to "value".
        """
        self.loop.run_until_complete(self.model.set(key, item))

    def get(self, key: str) -> str | None:
        """Query a key from the provided redis server and return its value.

        Parameters
        ----------
        key : str
            Key that will be used to query the stored data.

        Return
        ------
        str
            Queried value. Returns None if value is not found.
        """
        return self.loop.run_until_complete(self.model.get(key))


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
    redis_address: str = field(
        default=os.getenv("BACKPACK_REDIS_URL", "redis://localhost:6379/0")
    )
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

    def __init__(
        self, source: DataSource, redis_address: str = "default"
    ) -> None:
        self.source = source
        self.config = DispatcherConfig()
        self.schema = Template(source.schema).substitute(
            {
                "namespace": self.config.namespace,
            }
        )
        self.redis = RedisManager(
            self.config.redis_address
            if redis_address == "default"
            else redis_address
        )

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
            "topic_name": f"{self.config.namespace}.{self.source.topic_name}",
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

    def _get_source_records(self) -> list[dict] | None:
        """Get source records and check the redis server for any
        duplicate data points present, then return a list with them removed.
        Returns None if list is empty.

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
        records = self.source.get_records()

        if len(records) == 0:
            return None

        if not self.source.uses_redis:
            return records

        return [
            record
            for record in records
            if self.redis.get(self.source.get_redis_key(record)) is None
        ]

    def post(self) -> tuple[str, list]:
        """Assemble schema and payload from the given source, then
        makes a POST request to kafka.

        Returns
        -------
        response-text : str
            The results of the POST request in string format
        records : list
            List of earthquakes with those already stored on remote removed
        """
        records = self._get_source_records()

        if records is None:
            return (
                "Warning: No entries found, aborting POST request",
                [],
            )

        if len(records) == 0:
            return (
                "Warning: All entries already present, aborting POST request",
                records,
            )

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
            return f"Error POSTing data: {e}", records

        if self.source.uses_redis:
            for record in records:
                self.redis.store(self.source.get_redis_key(record))

        return response.text, records
