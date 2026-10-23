"""Rebuild gw_data's house_operating_status projection from the journal.

Not part of normal operation: live messages keep a running journalkeeper's
projection current. Run this after the migration that adds the table and
whenever the table is suspect. Every house with a layouts row gets a
derived status from that layout and its newest journaled snapshot; then
the newest journaled ``gw.house.operating.status`` of each sender is
projected over it, so a house whose scada sends the word ends with a
``scada`` row. No ``messages`` row is written.

Run from the repo root::

    uv run python -m gjk.rebuild_house_status
"""

from __future__ import annotations

import logging

import dotenv
from gw_data.db.models import LayoutSql, MessageSql
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from gjk.config import Settings
from gjk.house_status_projection import HouseStatusProjection
from gjk.sema.types import GwHouseOperatingStatus

LOGGER = logging.getLogger("rebuild_house_status")
STATUS = "gw.house.operating.status"


def newest_status_messages(db: Session) -> list[MessageSql]:
    """The newest journaled gw.house.operating.status row for each sender."""
    newest = (
        db
        .query(MessageSql.from_alias, func.max(MessageSql.timestamp).label("ts"))
        .filter(MessageSql.message_type_name == STATUS)
        .group_by(MessageSql.from_alias)
        .subquery()
    )
    return (
        db
        .query(MessageSql)
        .join(
            newest,
            (MessageSql.from_alias == newest.c.from_alias)
            & (MessageSql.timestamp == newest.c.ts),
        )
        .filter(MessageSql.message_type_name == STATUS)
        .all()
    )


def rebuild(db: Session, projection: HouseStatusProjection) -> tuple[int, int]:
    """Derive for every house with a layout, then project each sender's
    newest status word; the counts (derived, reported)."""
    derived = 0
    for layout_row in db.query(LayoutSql).all():
        if projection.derive(db, layout_row.terminal_asset_alias):
            derived += 1
    reported = 0
    for msg in newest_status_messages(db):
        status = projection.codec.from_dict(msg.payload)
        assert isinstance(status, GwHouseOperatingStatus)
        projection.project_reported(db, msg.from_alias, status, str(msg.id))
        reported += 1
    return derived, reported


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    settings = Settings(_env_file=dotenv.find_dotenv())  # type: ignore
    engine = create_engine(settings.db_url.get_secret_value())
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db, db.begin():
        derived, reported = rebuild(db, HouseStatusProjection(LOGGER))
    LOGGER.info(
        "derived %d house status row(s); projected %d reported status word(s)",
        derived,
        reported,
    )
    engine.dispose()


if __name__ == "__main__":
    main()
