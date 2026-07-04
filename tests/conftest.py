"""Shared fixtures for gjk tests.

The ``integration`` fixtures stand up ephemeral docker services (TimescaleDB,
RabbitMQ) via ``testcontainers`` and tear them down when the session ends. They
self-skip when docker is unavailable so the unit suite still runs anywhere.
"""

from __future__ import annotations

import subprocess
import time

import pytest
from sqlalchemy import create_engine, text


def _docker_available() -> bool:
    try:
        return subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).returncode == 0
    except Exception:  # noqa: BLE001 -- any failure => treat docker as absent
        return False


def _wait(fn, timeout: float, what: str) -> None:
    """Poll ``fn`` (which raises until ready) until it succeeds or we time out."""
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            fn()
            return
        except Exception as e:  # noqa: BLE001 -- readiness probe; keep last error
            last = e
            time.sleep(1)
    raise RuntimeError(f"{what} never became ready: {last!r}")


def _create_gw_data_schema(db_url: str) -> None:
    """Create the ``gridworks`` schema + tables the persistor writes to.

    The TimescaleDB hypertable arg on ``messages`` is ignored by plain
    ``create_all`` (no sqlalchemy-timescaledb dialect installed), so the table
    is created as a regular table — which is all this functional test needs.
    """
    import gw_data.db.models  # noqa: F401 -- registers models on Base.metadata
    from gw_data.db.models._base import Base

    eng = create_engine(db_url)
    with eng.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        c.execute(text("CREATE SCHEMA IF NOT EXISTS gridworks"))
    Base.metadata.create_all(eng)
    eng.dispose()


@pytest.fixture(scope="session")
def timescale_db_url() -> str:
    if not _docker_available():
        pytest.skip("docker not available")
    from testcontainers.core.container import DockerContainer

    container = (
        DockerContainer("timescale/timescaledb-ha:pg16")
        .with_env("POSTGRES_PASSWORD", "test")
        .with_env("POSTGRES_DB", "tsdb")
        .with_exposed_ports(5432)
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5432)
        url = f"postgresql+psycopg2://postgres:test@{host}:{port}/tsdb"

        def _probe() -> None:
            eng = create_engine(url)
            with eng.connect() as c:
                c.execute(text("SELECT 1"))
            eng.dispose()

        _wait(_probe, timeout=60, what="timescaledb")
        _create_gw_data_schema(url)
        yield url
    finally:
        container.stop()


@pytest.fixture(scope="session")
def rabbit_url() -> str:
    if not _docker_available():
        pytest.skip("docker not available")
    import pika
    from testcontainers.core.container import DockerContainer

    # NB: a non-"guest" user, because rabbit restricts "guest" to loopback —
    # testcontainers connects over the mapped port, which rabbit sees as remote.
    container = (
        DockerContainer("rabbitmq:3.13")
        .with_env("RABBITMQ_DEFAULT_USER", "tester")
        .with_env("RABBITMQ_DEFAULT_PASS", "tester")
        .with_exposed_ports(5672)
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5672)
        url = f"amqp://tester:tester@{host}:{port}/"

        def _probe() -> None:
            conn = pika.BlockingConnection(pika.URLParameters(url))
            conn.close()

        _wait(_probe, timeout=60, what="rabbitmq")
        yield url
    finally:
        container.stop()
