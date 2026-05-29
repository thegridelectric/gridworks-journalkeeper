"""HACK (2026-05-27): point JournalKeeper at the PROD broker and just
observe — count distinct type_names received over a fixed window,
then exit. No persistence (DB writes wrapped in try/except).

Companion to scripts/point_at_dev_hack.py. UNTRACKED in spirit (only
exists for the stored-vs-not-stored inventory captured into
wiki/gridworks-journalkeeper/executor/primary.md). Remove once the
proper test harness lands.

Run from repo root:
    uv run python scripts/point_at_prod_observe.py [seconds=600]
"""
from __future__ import annotations

import logging
import sys
import time
from collections import Counter
from pathlib import Path

import dotenv

# .env already points GJK_RABBIT__URL at prod for this branch (jm/db_v2).
dotenv.load_dotenv(dotenv.find_dotenv(), override=False)

from gjk.config import Settings  # noqa: E402
from gjk.journal_keeper import JournalKeeper  # noqa: E402
from gjk.sema import SemaCodec  # noqa: E402

OBSERVE_SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 600  # 10 min default
CAPTURE_DIR = Path(__file__).resolve().parent.parent / "captured-prod-observe"
CAPTURE_DIR.mkdir(exist_ok=True)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("point_at_prod_observe")

    settings = Settings()
    # Mask creds generically — never hardcode the password as a literal.
    import re
    safe_url = re.sub(r"://([^:]+):[^@]+@", r"://\1:***@", settings.rabbit.url.get_secret_value())
    logger.info("Broker URL: %s", safe_url)
    codec = SemaCodec()
    jk = JournalKeeper(settings, codec, logger)

    counts: Counter = Counter()
    persist_failures: Counter = Counter()
    distinct_from: set[str] = set()

    def catchall_startup() -> None:
        logger.info(
            "[catch-all prod] Binding %s on %s with #",
            jk.queue_name,
            jk._consume_exchange,
        )
        jk._single_channel.queue_bind(
            jk.queue_name, jk._consume_exchange, routing_key="#"
        )

    jk.local_rabbit_startup = catchall_startup  # type: ignore[method-assign]

    original_dispatch = jk.dispatch_message

    def counting_dispatch(*, envelope: object, body: bytes) -> None:
        type_name = getattr(envelope, "type_name", "unknown")
        from_alias = getattr(envelope, "from_alias", "unknown")
        counts[type_name] += 1
        distinct_from.add(from_alias)
        try:
            original_dispatch(envelope=envelope, body=body)  # type: ignore[arg-type]
        except Exception as e:
            persist_failures[type_name] += 1
            # quiet — this is the very thing we're inventorying
            del e

    jk.dispatch_message = counting_dispatch  # type: ignore[method-assign]

    logger.info("Starting prod observation for %ds...", OBSERVE_SECONDS)
    jk.start()
    deadline = time.time() + OBSERVE_SECONDS
    try:
        while jk.main_loop_running and time.time() < deadline:
            time.sleep(5)
            total = sum(counts.values())
            if total and int(time.time()) % 60 < 5:
                logger.info("...so far: %d msgs across %d types from %d aliases",
                            total, len(counts), len(distinct_from))
    except KeyboardInterrupt:
        pass
    finally:
        jk.stop()

    # Final report
    print("\n" + "=" * 60)
    print(f"OBSERVATION REPORT ({OBSERVE_SECONDS}s)")
    print("=" * 60)
    print(f"Total messages: {sum(counts.values())}")
    print(f"Distinct types: {len(counts)}")
    print(f"Distinct from_aliases: {len(distinct_from)}")
    print()
    print(f"{'type_name':<50} {'count':>8} {'persist_failed':>15}")
    print("-" * 75)
    for type_name, count in counts.most_common():
        pf = persist_failures.get(type_name, 0)
        print(f"{type_name:<50} {count:>8} {pf:>15}")
    print()
    print(f"Distinct from_aliases ({len(distinct_from)}):")
    for alias in sorted(distinct_from):
        print(f"  {alias}")


if __name__ == "__main__":
    main()
