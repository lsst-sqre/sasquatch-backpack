# from datetime import timedelta
from string import Template

import requests

# from sasquatchbackpack.scripts import *


class sasquatchdeploy:
    """help"""

    def __init__(self, namespace: str, topic_name: str):
        self._namespace = namespace
        self._topic_name = topic_name

    def build_payload(self) -> list:
        return []

    def create_kafka_topic(self) -> str:
        sasquatch_rest_proxy_url = (
            "https://data-int.lsst.cloud/sasquatch-rest-proxy"
        )

        headers = {"content-type": "application/json"}

        r = requests.get(
            f"{sasquatch_rest_proxy_url}/v3/clusters", headers=headers
        )

        cluster_id = r.json()["data"][0]["cluster_id"]

        # The topic is created with one partition and a replication
        # factor of 3 by default, this configuration is fixed for the '
        # Sasquatch Kafka cluster.
        topic_config = {
            "topic_name": f"{self._namespace}.{self._topic_name}",
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

    def send_data(self):
        sasquatch_rest_proxy_url = (
            "https://data-int.lsst.cloud/sasquatch-rest-proxy"
        )

        with open("src/sasquatchbackpack/schemas/usgs.avsc", "r") as file:
            template = Template(file.read())

        value_schema = template.substitute(
            {"namespace": "lsst.example", "topic_name": "usgs-earthquake-data"}
        )

        url = f"{sasquatch_rest_proxy_url}/topics/"
        +"{self._namespace}.{self._topic_name}"

        headers = {
            "Content-Type": "application/vnd.kafka.avro.v2+json",
            "Accept": "application/vnd.kafka.v2+json",
        }

        results = self.build_payload()

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

        payload = {"value_schema": value_schema, "records": records}

        print(payload)

        response = requests.request("POST", url, json=payload, headers=headers)

        return response
