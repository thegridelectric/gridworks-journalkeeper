"""Rebuild gw_data's layouts projection from the journal.

Not part of normal operation: a live ``layout.lite`` keeps a running
journalkeeper's projection current. Run this after the migration that
adds ``layouts``, so the table is full before any scada reconnects, and
whenever the table is suspect. The projection is rebuildable at any time
from the raw messages, which is what makes it a projection.

For every sender of ``layout.lite`` the newest journaled message is
decoded and projected through the same path a live message takes
(``LayoutsProjection.project``). No ``messages`` row is written.

Run from the repo root::

    uv run python -m gjk.rebuild_layouts
"""

from __future__ import annotations

import logging

import dotenv
from gw_data.db.models import MessageSql
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from gjk.config import Settings
from gjk.layouts_projection import LayoutsProjection
from gjk.sema.codec import SemaCodec

LOGGER = logging.getLogger("rebuild_layouts")
LAYOUT_LITE = "layout.lite"


def newest_layout_messages(db: Session) -> list[MessageSql]:
    """The newest journaled layout.lite row for each sender."""
    newest = (
        db
        .query(MessageSql.from_alias, func.max(MessageSql.timestamp).label("ts"))
        .filter(MessageSql.message_type_name == LAYOUT_LITE)
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
        .filter(MessageSql.message_type_name == LAYOUT_LITE)
        .all()
    )


def rebuild(db: Session, codec: SemaCodec, projection: LayoutsProjection) -> int:
    """Project each sender's newest layout.lite; the number projected."""
    count = 0
    for msg in newest_layout_messages(db):
        layout = codec.from_dict(msg.payload, auto_upgrade=False)
        projection.project(db, msg.from_alias, layout)
        count += 1
    return count


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    settings = Settings(_env_file=dotenv.find_dotenv())  # type: ignore
    engine = create_engine(settings.db_url.get_secret_value())
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db, db.begin():
        count = rebuild(db, SemaCodec(), LayoutsProjection(LOGGER))
    LOGGER.info("projected the newest layout.lite of %d sender(s)", count)
    engine.dispose()


if __name__ == "__main__":
    main()
