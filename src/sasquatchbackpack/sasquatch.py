"""Handles dispatch of backpack data to kafka."""

__all__ = ["BackpackDispatcher", "DispatcherConfig"]

import os
from dataclasses import dataclass
from string import Template

import requests

from sasquatchbackpack import sources

# Code yoinked from https://github.com/lsst-sqre/
# sasquatch/blob/main/examples/RestProxyAPIExample.ipynb


@dataclass
class DispatcherConfig:
    """Class containing relevant configuration information for the
    BackpackDispatcher.

    Values
    ------
    sasquatch_rest_proxy_url
        environment variable contatining the target for data
    partitions_count
        number of partitions to create
    replication_factor
        number of replicas to create
    namespace
        environment varible containing the target namespace
    """

    sasquatch_rest_proxy_url = os.getenv(
        "SASQUATCH_REST_PROXY_URL",
        "https://data-int.lsst.cloud/sasquatch-rest-proxy",
    )
    partitions_count = 1
    replication_factor = 3
    namespace = os.getenv("BACKPACK_NAMESPACE", "lsst.backpack")


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
        self.schema = Template(source.load_schema()).substitute(
            {
                "namespace": self.config.namespace,
                "topic_name": self.source.topic_name,
            }
        )

    def create_topic(self) -> str:
        """Create kafka topic based off data from provided source.

        Returns
        -------
        str
            The results of the POST request in string format
        """
        headers = {"content-type": "application/json"}

        r = requests.get(
            f"{self.config.sasquatch_rest_proxy_url}/v3/clusters",
            headers=headers,
            timeout=10,
        )

        cluster_id = r.json()["data"][0]["cluster_id"]

        topic_config = {
            "topic_name": f"{self.config.namespace}."
            f"{self.source.topic_name}",
            "partitions_count": self.config.partitions_count,
            "replication_factor": self.config.replication_factor,
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

    def post(self) -> str:
        """Assemble schema and payload from the given source, then
        makes a POST request to kafka.

        Returns
        -------
        str
            The results of the POST request in string format
        """
        records = self.source.get_records()

        payload = {"value_schema": self.schema, "records": records}

        url = (
            f"{self.config.sasquatch_rest_proxy_url}/topics/"
            f"{self.config.namespace}.{self.source.topic_name}"
        )

        headers = {
            "Content-Type": "application/vnd.kafka.avro.v2+json",
            "Accept": "application/vnd.kafka.v2+json",
        }

        response = requests.request(
            "POST",
            url,
            json=payload,
            headers=headers,
            timeout=10,
        )
        return response.text
