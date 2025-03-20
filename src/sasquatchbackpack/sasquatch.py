"""Handles dispatch of backpack data to kafka."""

__all__ = ["BackpackDispatcher", "DataSource", "DispatcherConfig"]

import asyncio
import json
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
                "topic_name": self.source.topic_name,
            }
        )
        self.redis = RedisManager(
            self.config.redis_address
            if redis_address == "default"
            else redis_address
        )

    def _get_topic_exists(self) -> bool | str:
        """Determine whether a topic exists on kafka already.

        Returns
        -------
        exists : bool | str
            True if this Dispatcher's topic exists in the proper rest proxy,
            otherwise, False. Will return a str containing relevant responses
            in the event of an error.
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

        headers = {"content-type": "application/json"}

        try:
            response = requests.get(
                f"{self.config.sasquatch_rest_proxy_url}/v3/clusters/"
                f"{cluster_id}/topics",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()  # Raises HTTPError for bad responses
            topics = response.json()["data"]
        except requests.RequestException as e:
            return f"Error Creating Topic during POST: {e}"

        topic_name = self.config.namespace + "." + self.source.topic_name

        return bool(any(topic["topic_name"] == topic_name for topic in topics))

    def _handle_topic_exists(
        self, request: dict[str, dict[str, str]]
    ) -> bool | None:
        """Handle errors and format responses for topic checking.

        Parameters
        ----------
        request: dict[str, dict[str, str]]
            Request item.

        Return
        ------
        bool | None
            boolean representation of whether this item's topic was found
            in kafka. None if an error was encountered.
        """
        topic_exists: bool | str = self._get_topic_exists()

        if type(topic_exists) is str:
            request["check_topic"] = {
                "status": "Error",
                "message": f"Topic check failed: \n{topic_exists}",
            }
            return None

        request["check_topic"] = {
            "status": "Success",
            "message": f'Sasquatch backpack {
                "found" if topic_exists else "did not find"
            } "{
                self.config.namespace + "." + self.source.topic_name
            }" on remote.',
        }
        return bool(topic_exists)

    def _post_new_topic(self) -> dict[str, str]:
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
            return {
                "status": "Error",
                "message": f"Error getting cluster ID: {e}",
            }

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
            return {
                "status": "Error",
                "message": f"Error Creating Topic during POST: {e}",
            }

        return {"status": "Success", "message": response.text}

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

    def post(self, *, force_post: bool = False) -> str:
        """Assemble schema and payload from the given source, then
        makes a POST request to kafka.

        Parameters
        ----------
        force_post: bool
            Ignore checks to determine whether a topic exists and
            push a new topic name, overwriting any extant topic names.

        Returns
        -------
        response: str
            stringified json containing the following key value pairs:
            "succeeded": bool
                True if the post succeeded,
                False if any relevant steps failed.
            "requests": dict[str, dict[str, str]]
                The results of various POST requests sent by this function.
                Empty values denote a POST request that has not occurred.
                "check_topic", create_topic", "write_values": dict
                    "status": str
                        "Success" if request suceeded, "Error" if request
                        failed, "Warning" for other non-breaking behavior.
                    "message": str
                        Specific description of what occured.
            "records": list
                List of posted records.
        """
        response: dict = {
            "succeeded": False,
            "requests": {
                "check_topic": {},
                "create_topic": {},
                "write_values": {},
            },
            "records": [],
        }
        requests = response["requests"]

        topic_exists = self._handle_topic_exists(requests)

        if topic_exists is None:
            return json.dumps(response)

        if force_post or not topic_exists:
            requests["create_topic"] = self._post_new_topic()
            if requests["create_topic"]["status"] == "Error":
                return json.dumps(response)
        else:
            requests["create_topic"] = {
                "status": "Success",
                "message": (
                    "Relevant topic already exists in kafka, "
                    "bypassing creation POST request."
                ),
            }

        records = self._get_source_records()

        if records is None:
            requests["write_values"] = {
                "status": "Warning",
                "message": "No entries found, aborting POST request",
            }
            return json.dumps(response)

        if len(records) == 0:
            requests["write_values"] = {
                "status": "Warning",
                "message": (
                    "All entries already present, aborting POST request"
                ),
            }
            return json.dumps(response)

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
            post_response = requests.request(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=10,
            )
            # Raises HTTPError for bad responses
            post_response.raise_for_status()

        except requests.RequestException as e:
            response["write_values"] = {
                "status": "Error",
                "message": f"Error writing values during POST: {e}",
            }
            return json.dumps(response)

        if self.source.uses_redis:
            for record in records:
                self.redis.store(self.source.get_redis_key(record))

        response["write_values"] = {
            "status": "Success",
            "message": post_response.text,
        }
        return json.dumps(response)
