from string import Template

import requests

from sasquatchbackpack import sources

# Code yoinked from https://github.com/lsst-sqre/
# sasquatch/blob/main/examples/RestProxyAPIExample.ipynb


class sasquatch_deploy:
    """A class to send backpack data to kafka.

    Parameters
    ----------
    source
        data_source containing the payload and other important,
        individulized data
    """

    def __init__(self, source: sources.data_source):
        self.source = source

    def create_kafka_topic(self) -> str:
        """Creates kafka topic based off data from provided source

        Returns
        -------
        response text
            The results of the POST request in string format
        """
        sasquatch_rest_proxy_url = (
            "https://data-int.lsst.cloud/sasquatch-rest-proxy"
        )

        headers = {"content-type": "application/json"}

        r = requests.get(
            f"{sasquatch_rest_proxy_url}/v3/clusters", headers=headers
        )

        cluster_id = r.json()["data"][0]["cluster_id"]

        # The topic is created with one partition and a replication
        # factor of 3 by default, this configuration is fixed for the
        # Sasquatch Kafka cluster.
        topic_config = {
            "topic_name": f"{self.source.namespace}."
            + f"{self.source.topic_name}",
            "partitions_count": 1,
            "replication_factor": 3,
        }

        headers = {"content-type": "application/json"}

        response = requests.post(
            f"{sasquatch_rest_proxy_url}/v3/clusters/{cluster_id}/topics",
            json=topic_config,
            headers=headers,
        )
        return response.text

    def send_data(self) -> dict:
        """Assemble schema and payload, then make a POST request to kafka

        Returns
        -------
        response text
            The results of the POST request in string format
        """
        with open(self.source.schema_directory, "r") as file:
            template = Template(file.read())

        value_schema = template.substitute(
            {
                "namespace": self.source.namespace,
                "topic_name": self.source.topic_name,
            }
        )

        # Currently unused, TODO: Uncomment when POSTing begins

        # url = f"{sasquatch_rest_proxy_url}/topics/"
        #       + f"{self.source.namespace}.{self.source.topic_name}"
        # headers = {
        #     "Content-Type": "application/vnd.kafka.avro.v2+json",
        #     "Accept": "application/vnd.kafka.v2+json",
        # }
        # sasquatch_rest_proxy_url = (
        #     "https://data-int.lsst.cloud/sasquatch-rest-proxy"
        # )

        records = self.source.get_records()

        payload = {"value_schema": value_schema, "records": records}

        # Temporarily returns payload instead of making full
        # POST request.
        # TODO: Once complete, delete and uncomment the following
        return payload

        # response = requests.request("POST",
        #                             url,
        #                             json=payload,
        #                             headers=headers
        #                             )
        # return response.text
