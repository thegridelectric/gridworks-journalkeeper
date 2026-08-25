"""Re-derive the flo.params.house0 pseudo-readings for rows already in the DB.

Prod holds flo.params.house0 v004–v006 from Jan 9 to Mar 2 2026 persisted
by the default path, before `persist_v004`–`persist_v006` existed — the
messages rows are there, the `buffer-available-kwh` / `lmp` / `total`
readings are not. Re-importing from S3 would be wasteful; this replays each
stored payload through the codec and the persistor: the messages insert is
`on_conflict_do_nothing`, so only `add_readings` does new work, and the
readings insert is itself conflict-free. Safe to rerun.

    GJK_DB_URL=<writer url> uv run python scripts/replay_flo_params.py [--dry-run]
"""

import argparse
import logging
import os

from gw_data.db.models import MessageSql
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gjk.config import Settings
from gjk.sema import SemaCodec, SemaType
from gjk.sema_message_persistor import SemaMessagePersistor

TYPE_NAME = "flo.params.house0"
VERSIONS = ("004", "005", "006")
BATCH = 200


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--versions",
        default=",".join(VERSIONS),
        help="comma-separated payload versions (dev testing)",
    )
    args = parser.parse_args()
    versions = tuple(args.versions.split(","))
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logger = logging.getLogger("replay")
    settings = Settings(service_alias="gjk.replay", _env_file=None)  # type: ignore
    codec = SemaCodec()
    persistor = SemaMessagePersistor(settings, codec, logger)
    engine = create_engine(os.environ["GJK_DB_URL"])
    with Session(engine) as db:
        rows = db.scalars(
            select(MessageSql)
            .where(MessageSql.message_type_name == TYPE_NAME)
            .where(MessageSql.payload["Version"].astext.in_(versions))
            .order_by(MessageSql.timestamp)
        ).all()
    logger.info(f"{len(rows)} {TYPE_NAME} rows at versions {versions}")
    batch: list[tuple[str, object, SemaType]] = []
    done = 0
    for row in rows:
        obj = codec.from_dict(row.payload, auto_upgrade=False)
        assert isinstance(obj, SemaType)
        batch.append((row.from_alias, row.persisted_at, obj))
        if len(batch) >= BATCH:
            if not args.dry_run:
                failures = persistor.persist_messages(batch)  # type: ignore[arg-type]
                for f in failures:
                    logger.error(
                        f"replay failed for {f[2].type_name} from {f[0]}: {f[3]!r}"
                    )
            done += len(batch)
            logger.info(f"replayed {done}/{len(rows)}")
            batch.clear()
    if batch and not args.dry_run:
        persistor.persist_messages(batch)  # type: ignore[arg-type]
    logger.info("done")


if __name__ == "__main__":
    main()
