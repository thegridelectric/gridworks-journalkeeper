"""JournalKeeper

Persists inbound RabbitMQ AMQP messages into the gw_data postgres schema
via SemaCodec + SemaMessagePersistor. The live AMQP path mirrors the
S3 backfill path implemented in :mod:`gjk.s3_message_importer`.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import UTC, datetime

from gwbase.actor_base import ActorBase
from gwbase.transport_encoding import RoutingEnvelope

from gjk.config import Settings
from gjk.sema import SemaCodec, SemaType
from gjk.sema_message_persistor import SemaMessagePersistor

LOGGER = logging.getLogger(__name__)


class JournalKeeper(ActorBase):
    def __init__(
        self,
        settings: Settings,
        codec: SemaCodec,
        logger: logging.Logger = LOGGER,
    ) -> None:
        super().__init__(settings=settings)
        self.settings: Settings = settings
        self.codec: SemaCodec = codec
        self.logger: logging.Logger = logger
        self.persistor: SemaMessagePersistor = SemaMessagePersistor(
            settings, codec, logger
        )
        self._consume_exchange = "ear_tx"
        self.main_thread = threading.Thread(target=self.main, daemon=True)

    # ------------------------------------------------------------------
    # Framework hooks
    # ------------------------------------------------------------------

    def local_rabbit_startup(self) -> None:
        """Bind one routing key per type the persistor knows how to handle.

        The persistor's ``all_known_message_types()`` is the single
        source of truth — new types added to the persistor's tables
        flow through automatically with no edits here.
        """
        for type_name in sorted(self.persistor.all_known_message_types()):
            routing_key = f"#.{type_name.replace(".", "-")}"
            self.logger.info(
                "Binding queue %s to %s with routing key %s",
                self.queue_name,
                self._consume_exchange,
                routing_key,
            )
            self._single_channel.queue_bind(
                self.queue_name,
                self._consume_exchange,
                routing_key=routing_key,
            )

    def local_start(self) -> None:
        self._main_loop_running = True
        self.main_thread.start()

    def local_stop(self) -> None:
        self._main_loop_running = False
        self.main_thread.join()

    # ------------------------------------------------------------------
    # Message dispatch
    # ------------------------------------------------------------------

    def dispatch_message(self, *, envelope: RoutingEnvelope, body: bytes) -> None:
        """Parse with SemaCodec, hand the SemaType to the persistor.

        Live AMQP counterpart to ``s3_message_importer.main()``'s loop.
        Errors are logged and swallowed — the live path keeps running,
        unlike the importer (which halts on first failure).
        """
        self._persist_body(from_alias=envelope.from_alias, body=body)

    def on_routing_key_parse_error(
        self, *, routing_key: str, body: bytes, error: ValueError
    ) -> None:
        """legacy_hack (PERMANENT) — salvage the pre-gwbase LTN ``broadcast.*``
        keys instead of letting gwbase drop them.

        Before the LTN became a gwbase actor it published several types with
        ``Dst="broadcast"`` (a magic string), so the wire routing key carries a
        ``broadcast`` token and is not a valid GridWorks envelope — gwbase's
        parser raises, and the body would be lost (the data-loss this and the
        gridworks-base design 'must-accept-current-ltn-messages' exist to stop).
        We recognize that shape and persist anyway, deriving the source from the
        wrapped body's ``Header.Src`` (the legacy key has no from-alias slot).

        Kept **permanently** (not an interim bridge): historical and replayed
        ``broadcast.*`` data must keep loading. Once the LTN emits a real
        gw-wrapped message (scada design 'ltn-sends-gw-wrapped') no *new*
        ``broadcast.*`` arrives live, but backfill/replay still depends on this
        branch. Anything that is not the legacy broadcast shape falls back to the
        base log+drop.
        """
        # The exact wire position of the `broadcast` token is still being
        # confirmed against prod (design 'ltn-sends-gw-wrapped' open question),
        # so match it anywhere in the key rather than only at token[0].
        if "broadcast" in routing_key.split("."):
            from_alias = self._legacy_src_from_body(body)
            self.logger.warning(
                f"legacy_hack: persisting legacy broadcast key {routing_key!r} "
                f"from {from_alias}"
            )
            self._persist_body(from_alias=from_alias, body=body)
            return
        super().on_routing_key_parse_error(
            routing_key=routing_key, body=body, error=error
        )

    @staticmethod
    def _legacy_src_from_body(body: bytes) -> str:
        """Best-effort source alias from a wrapped body's ``Header.Src``; the
        legacy ``broadcast.*`` key carries no from-alias slot."""
        try:
            header = json.loads(body.decode("utf-8")).get("Header", {})
            src = header.get("Src")
            if isinstance(src, str) and src:
                return src
        except Exception:  # noqa: BLE001 -- best-effort; fall through to default
            pass
        return "unknown.broadcast.src"

    def _persist_body(self, *, from_alias: str, body: bytes) -> None:
        """Decode a wrapped message body and hand the SemaType to the persistor.
        Shared by the normal dispatch path and the broadcast ``legacy_hack``.
        Errors are logged and swallowed — the live path keeps running."""
        try:
            msg_dict = json.loads(body.decode("utf-8"))
        except Exception as e:
            self.logger.error(
                f"Failed to decode body as JSON from {from_alias}: {e!r}"
            )
            return

        # Messages on ear_tx come wrapped: { "Payload": {...}, ... }.
        # Tolerate the rare unwrapped case (incoming dict already a SemaType).
        payload_dict = msg_dict.get("Payload", msg_dict)

        try:
            sema_obj = self.codec.from_dict(
                payload_dict, auto_upgrade=False, mode="degraded"
            )
        except Exception as e:
            self.logger.error(f"Codec decode failed from {from_alias}: {e!r}")
            return

        if not isinstance(sema_obj, SemaType):
            self.logger.warning(
                f"Got degraded SEMA type {sema_obj.type_name} "
                f"(v{sema_obj.version}) from {from_alias} — not persisting"
            )
            return

        try:
            self.persistor.persist_message(from_alias, datetime.now(UTC), sema_obj)
        except Exception as e:
            self.logger.error(
                f"Persist failed for {sema_obj.type_name} "
                f"from {from_alias}: {e!r}"
            )

    # ------------------------------------------------------------------
    # Background loop (placeholder)
    # ------------------------------------------------------------------

    def main(self) -> None:
        # Reserved for periodic S3 catch-up of missed messages
        # (see s3_message_importer for the import shape).
        while self._main_loop_running:
            time.sleep(3600)
