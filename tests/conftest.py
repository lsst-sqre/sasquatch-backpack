"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.admin.client import AIOKafkaAdminClient
from faststream.kafka import KafkaBroker
from safir.kafka import KafkaConnectionSettings, SecurityProtocol
from safir.testing.containers import FullKafkaContainer
from testcontainers.core.network import Network


@pytest.fixture(scope="session")
def kafka_docker_network() -> Iterator[Network]:
    with Network() as network:
        yield network


@pytest.fixture(scope="session")
def global_kafka_container(
    kafka_docker_network: Network,
) -> Iterator[FullKafkaContainer]:
    container = FullKafkaContainer()
    container.with_network(kafka_docker_network)
    container.with_network_aliases("kafka")
    with container as kafka:
        yield kafka


@pytest.fixture
def kafka_container(
    global_kafka_container: FullKafkaContainer,
) -> Iterator[FullKafkaContainer]:
    global_kafka_container.reset()
    return global_kafka_container


@pytest.fixture
def kafka_connection_settings(
    kafka_container: FullKafkaContainer,
) -> KafkaConnectionSettings:
    return KafkaConnectionSettings(
        bootstrap_servers=kafka_container.get_bootstrap_server(),
        security_protocol=SecurityProtocol.PLAINTEXT,
    )


@pytest_asyncio.fixture
async def kafka_consumer(
    kafka_connection_settings: KafkaConnectionSettings,
) -> AsyncGenerator[AIOKafkaConsumer]:
    consumer = AIOKafkaConsumer(
        **kafka_connection_settings.to_aiokafka_params(),
        client_id="pytest-consumer",
    )
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture
async def kafka_admin_client(
    kafka_connection_settings: KafkaConnectionSettings,
) -> AsyncGenerator[AIOKafkaAdminClient]:
    client = AIOKafkaAdminClient(
        **kafka_connection_settings.to_aiokafka_params(),
        client_id="pytest-admin",
    )
    await client.start()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def kafka_broker(
    kafka_connection_settings: KafkaConnectionSettings,
) -> AsyncGenerator[KafkaBroker]:
    broker = KafkaBroker(
        **kafka_connection_settings.to_faststream_params(),
        client_id="pytest-broker",
    )
    await broker.start()
    yield broker
    await broker.stop()
