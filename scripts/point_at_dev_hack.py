"""HACK (2026-05-26): point JournalKeeper at the LOCAL dev rabbit
(gw-dev-rabbit) instead of prod. Companion to gwwf's hack-fictitious
mode — proves the gwwf→gjk weather path on dev infrastructure.

UNTRACKED — not part of the package. Remove once the proper
end-to-end dev recipe lands in wiki/gridworks-journalkeeper/.

Run from repo root:
    uv run python scripts/point_at_dev_hack.py
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import dotenv

# Override prod-broker .env BEFORE Settings(); dev rabbit creds per
# gridworks-scada/for_docker/dev_rabbitmq.conf.
os.environ["GJK_RABBIT__URL"] = "amqp://smqPublic:smqPublic@localhost:5672/d1__1"
dotenv.load_dotenv(dotenv.find_dotenv(), override=False)

from gjk.config import Settings  # noqa: E402
from gjk.journal_keeper import JournalKeeper  # noqa: E402
from gjk.sema import SemaCodec  # noqa: E402

CAPTURE_DIR = Path(__file__).resolve().parent.parent / "captured-dev"
CAPTURE_DIR.mkdir(exist_ok=True)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("point_at_dev_hack")

    settings = Settings()
    codec = SemaCodec()
    jk = JournalKeeper(settings, codec, logger)

    # Bind catch-all so we see whatever lands on ws_tx (where the
    # weathermic_tx → ws_tx e2e binding routes gwwf's publishes).
    def catchall_startup() -> None:
        logger.info(
            "[catch-all dev] Binding %s on %s with #",
            jk.queue_name,
            jk._consume_exchange,
        )
        jk._single_channel.queue_bind(
            jk.queue_name, jk._consume_exchange, routing_key="#"
        )

    jk.local_rabbit_startup = catchall_startup  # type: ignore[method-assign]

    # Capture + log every body that arrives, before the parse+persist path.
    original_dispatch = jk.dispatch_message

    def capturing_dispatch(*, envelope: object, body: bytes) -> None:
        ts = int(time.time() * 1000)
        from_alias = getattr(envelope, "from_alias", "unknown")
        type_name = getattr(envelope, "type_name", "unknown")
        logger.info(
            "RECEIVED type=%s from=%s body=%s",
            type_name,
            from_alias,
            body[:200].decode("utf-8", errors="replace"),
        )
        fname = CAPTURE_DIR / f"{from_alias}-{type_name}-{ts}.json"
        try:
            fname.write_bytes(body)
        except Exception as e:
            logger.warning(f"capture write failed: {e!r}")
        try:
            original_dispatch(envelope=envelope, body=body)  # type: ignore[arg-type]
        except Exception as e:
            logger.warning(
                f"dispatch (persist) failed (expected if DB schema missing): {e!r}"
            )

    jk.dispatch_message = capturing_dispatch  # type: ignore[method-assign]

    logger.info("Starting JournalKeeper against DEV broker (gw-dev-rabbit)...")
    jk.start()

    try:
        while jk.main_loop_running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupt received; stopping")
        jk.stop()


if __name__ == "__main__":
    main()
