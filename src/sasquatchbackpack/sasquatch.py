"""Handles dispatch of backpack data to kafka."""

import json
from dataclasses import dataclass

import requests

from sasquatchbackpack import sources

# Code yoinked from https://github.com/lsst-sqre/
# sasquatch/blob/main/examples/RestProxyAPIExample.ipynb


@dataclass
class DispatcherConfig:
    """Class containing relevant configuration information for the
    BackpackDispatcher.
    """

    sasquatch_rest_proxy_url = (
        "https://data-int.lsst.cloud/sasquatch-rest-proxy"
    )


class BackpackDispatcher:
    """A class to send backpack data to kafka.

    Parameters
    ----------
    source
        DataSource containing schema and record data to be
        posted to remote
    config
        DispatcherConfig to transmit other relevant information to
        the Dispatcher
    """

    def __init__(
        self, source: sources.DataSource, config: DispatcherConfig
    ) -> None:
        self.source = source
        self.config = config
        self.schema = source.load_schema()
        self.namespace = self.get_namespace()

    def get_namespace(self) -> str:
        """Sorts the schema and returns the namespace value.

        Returns
        -------
        namespace
            provided namespace from the schema file
        """
        json_schema = json.loads(self.schema)

        return json_schema["namespace"]

    def create_topic(self) -> str:
        """Create kafka topic based off data from provided source.

        Returns
        -------
        response text
            The results of the POST request in string format
        """
        headers = {"content-type": "application/json"}

        r = requests.get(
            f"{self.config.sasquatch_rest_proxy_url}/v3/clusters",
            headers=headers,
            timeout=10,
        )

        cluster_id = r.json()["data"][0]["cluster_id"]

        # The topic is created with one partition and a replication
        # factor of 3 by default, this configuration is fixed for the
        # Sasquatch Kafka cluster.
        topic_config = {
            "topic_name": f"{self.namespace}." + f"{self.source.topic_name}",
            "partitions_count": 1,
            "replication_factor": 3,
        }

        headers = {"content-type": "application/json"}

        response = requests.post(
            f"{self.config.sasquatch_rest_proxy_url}/v3/clusters/"
            f"{cluster_id}/topics",
            json=topic_config,
            headers=headers,
            timeout=10,
        )
        return response.text

    def post(self) -> dict:
        """Assemble schema and payload from the given source, then
        makes a POST request to kafka.

        Returns
        -------
        response text
            The results of the POST request in string format
        """
        records = self.source.get_records()

        payload = {"value_schema": self.schema, "records": records}

        # Temporary lint bypassing during testing
        # ruff: noqa: ERA001
        return payload  # noqa: RET504

        # url = f"{self.config.sasquatch_rest_proxy_url}/topics/"
        # f"{self.namespace}.{self.source.topic_name}"

        # headers = {
        #     "Content-Type": "application/vnd.kafka.avro.v2+json",
        #     "Accept": "application/vnd.kafka.v2+json",
        # }

        # response = requests.request("POST",
        #                             url,
        #                             json=payload,
        #                             headers=headers,
        #                             timeout=10,
        #                             )
        # return response.text
