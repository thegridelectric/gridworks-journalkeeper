import logging
import sys
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime

import dotenv
from gw_data.db.models import MessageSql
from sema.runtime import SemaCodec, SemaType
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.config import Settings
from gjk.layout_lite_persistor import LayoutLitePersistor
from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.report_event_persistor import ReportEventPersistor


class SemaMessagePersistor:
    def __init__(self, settings: Settings, codec: SemaCodec, logger):
        self.settings = settings
        self.codec = codec
        engine = create_engine(settings.db_url.get_secret_value(), echo=False)
        self.Session = sessionmaker(bind=engine)
        self.logger = logger

        self.persistor_lookup = {
            p.target_message_type: p
            for p in [
                LayoutLitePersistor(logger),
                ReportEventPersistor(logger),
            ]
        }

    @contextmanager
    def get_db(self):
        """Context manager to provide a new session for each task."""
        session = self.Session()
        try:
            yield session
            session.commit()  # Commit if everything went well
        except Exception:
            session.rollback()  # Rollback in case of an error
            raise  # Re-raise the exception after rollback
        finally:
            session.close()  # Always close the session

    def persist_message_default(self, from_alias: str, payload: SemaType):
        self.logger.warn(
            f"Default persistor called for message type {payload.type_name} v{payload.version}"
        )
        raise ValueError("persist_message_default")

    def persist_message(
        self, from_alias: str, time_received: datetime, payload: SemaType
    ):
        self.logger.debug(
            f"persisting message of type {payload.type_name}:{payload.version} from {from_alias} at {time_received.isoformat()}"
        )

        persist_fn: Callable[[str, SemaType], MessagePersistenceInfo] | None = None
        persistor = self.persistor_lookup.get(payload.type_name, None)
        if persistor is None:
            persist_fn = self.persist_message_default
        else:
            method_name = f"persist_v{payload.version}"
            persist_fn = getattr(persistor, method_name, self.persist_message_default)

        if persist_fn is None:
            raise ValueError("persist_fn is None")

        persistence_info = persist_fn(from_alias, payload)
        with self.get_db() as db:
            msg = MessageSql(
                id=uuid.UUID(persistence_info.id),
                timestamp=(
                    persistence_info.created_at
                    if persistence_info.created_at
                    else time_received
                ),
                created_at=persistence_info.created_at,
                persisted_at=time_received,
                from_alias=from_alias,
                message_type_name=payload.type_name,
                payload=payload.to_dict(),
            )
            db.add(msg)

            if persistence_info.additional_db_operations is not None:
                persistence_info.additional_db_operations(db)


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

    settings = Settings(_env_file=dotenv.find_dotenv())

    codec = SemaCodec()

    persistor = SemaMessagePersistor(settings, codec, logger)

    fn = "03a9b284-c040-4d75-859a-0ffbf12bc364-new-unit.json"
    with open(fn, "rb") as file:
        msg_bytes = file.read()
        sema_obj = codec.from_bytes(msg_bytes, auto_upgrade=False, mode="degraded")
        if isinstance(sema_obj, SemaType):
            persistor.persist_message(
                "hw1.isone.me.versant.keene.oak.scada",
                datetime.fromtimestamp(1776948541),
                sema_obj,
            )
        else:
            logger.error("unable to parse message")


if __name__ == "__main__":
    main()
