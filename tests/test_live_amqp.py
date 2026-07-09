"""Layer-2 liveness test: emitter -> broker -> JournalKeeper -> DB.

Stands up a real RabbitMQ + TimescaleDB (via the ``conftest`` fixtures), boots an
actual ``JournalKeeper`` actor against them, publishes a ``scada.params`` sample
to ``amq.topic`` (bridged into the actor's ``ear_tx`` consume exchange by an
exchange-to-exchange binding), and asserts the message routes through the broker,
is consumed + decoded + persisted, and lands as a ``gridworks.messages`` row.

This is the first test that runs JournalKeeper end-to-end against a real broker
and DB — and it doubles as the live verification of the ServiceSettings tap-tier
migration, because it actually executes ``ActorBase.__init__`` -> broker-consume
(the path the unit suite skips by constructing JK via ``__new__``).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pika
import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine, text

from gwbase.transport_encoding import gridworks_wrapped_routing_key

pytestmark = pytest.mark.integration

SAMPLE_TYPE = "scada.params"
SAMPLE_FILE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "gjk"
    / "sema"
    / "samples"
    / "scada.params.004.json"
)


def _declare_topology(amqp_url: str) -> None:
    """Pre-provision the fabric the actor's *passive* exchange declare asserts:
    a durable ``ear_tx`` topic exchange, bridged from the built-in ``amq.topic``
    so a publish to amq.topic flows into ear_tx (and thence to JK's queue)."""
    conn = pika.BlockingConnection(pika.URLParameters(amqp_url))
    ch = conn.channel()
    ch.exchange_declare(exchange="ear_tx", exchange_type="topic", durable=True)
    ch.exchange_bind(destination="ear_tx", source="amq.topic", routing_key="#")
    conn.close()


def test_emitter_through_broker_to_journalkeeper(
    timescale_db_url: str, rabbit_url: str, monkeypatch, tmp_path
) -> None:
    # The actor logger writes under XDG state-home; keep it inside tmp.
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    _declare_topology(rabbit_url)

    from gjk.config import Settings
    from gjk.journal_keeper import JournalKeeper
    from gjk.sema import SemaCodec
    from gwbase.config.rabbit_settings import RabbitBrokerClient

    settings = Settings(
        db_url=SecretStr(timescale_db_url),
        service_alias="d1.journal",
        rabbit=RabbitBrokerClient(url=SecretStr(rabbit_url)),
    )
    jk = JournalKeeper(settings=settings, codec=SemaCodec())
    jk.start()
    try:
        deadline = time.time() + 30
        while not jk.consuming and time.time() < deadline:
            time.sleep(0.2)
        assert jk.consuming, "JournalKeeper never started consuming"

        sample = json.loads(SAMPLE_FILE.read_text())
        body = json.dumps({"Payload": sample}).encode()
        routing_key = gridworks_wrapped_routing_key(
            from_alias="d1.isone.me.versant.keene.beech.scada",
            to_class_token="a",
            type_name=SAMPLE_TYPE,
        )

        conn = pika.BlockingConnection(pika.URLParameters(rabbit_url))
        pub = conn.channel()
        eng = create_engine(timescale_db_url)

        # publish-until-landed: scada.params has a payload-fixed id (message_id)
        # and timestamp (unix_time_ms), so republish is an idempotent
        # on_conflict_do_nothing no-op. That makes this safe against the
        # bind/consume race (the queue may not be bound on the first publish).
        landed = 0
        deadline = time.time() + 30
        while time.time() < deadline:
            pub.basic_publish(exchange="amq.topic", routing_key=routing_key, body=body)
            time.sleep(0.5)
            with eng.connect() as c:
                landed = c.execute(
                    text(
                        "SELECT count(*) FROM gridworks.messages "
                        "WHERE message_type_name = :t"
                    ),
                    {"t": SAMPLE_TYPE},
                ).scalar()
            if landed:
                break
        conn.close()
        eng.dispose()

        assert landed, f"{SAMPLE_TYPE} never landed in gridworks.messages"
    finally:
        # Best-effort: do NOT call jk.stop() — it joins the main thread, which
        # sleeps 3600s. Daemon threads + container teardown handle cleanup.
        jk._main_loop_running = False
        jk.shutting_down = True
        try:
            jk.stop_consumer()
        except Exception:  # noqa: BLE001 -- best-effort teardown
            pass
