import uuid
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime

from gw_data.db.models import MessageSql
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from gjk.config import Settings
from gjk.layout_lite_persistor import LayoutLitePersistor
from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.report_event_persistor import ReportEventPersistor
from gjk.sema import SemaCodec, SemaType


class SemaMessagePersistor:
    MSG_CREATED_AT_FIELDS_MS = {
        "glitch": "created_ms",
        "gridworks.event.problem": "time_created_ms",
        "energy.instruction": "send_time_ms",
        "new.command.tree": "unix_ms",
        "snapshot.spaceheat": "snapshot_time_unix_ms",
        "scada.params": "unix_time_ms",
        "ticklist.reed.report": "scada_received_unix_ms",
        "ticklist.hall.report": "scada_received_unix_ms",
        # Obsolete message types
        "report": "message_created_ms",
    }

    MSG_CREATED_AT_FIELDS_S = {
        "flo.params.house0": "params_generated_s",
        "heating.forecast": "forecast_created_s",
        "weather.forecast": "forecast_created_s",
    }

    MSG_ID_FIELDS = {
        "gridworks.event.problem": "message_id",
        "scada.params": "message_id",
        # Obsolete message types
        "report": "id",
    }

    # Messages with no id or created_at info, but we still want to persist
    BASIC_MSG_TYPES = [
        "atn.bid",
        "latest.price",
        "power.watts",
    ]

    def __init__(self, settings: Settings, codec: SemaCodec, logger):
        self.settings = settings
        self.codec = codec
        engine = create_engine(settings.db_url.get_secret_value(), echo=False)
        self.Session = sessionmaker(bind=engine)
        self.logger = logger

        self.custom_persistor_lookup = {
            x.target_message_type: x
            for x in [
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

    def all_known_message_types(self):
        return {
            *(
                self.BASIC_MSG_TYPES
                + list(self.MSG_CREATED_AT_FIELDS_S.keys())
                + list(self.MSG_CREATED_AT_FIELDS_MS.keys())
                + list(self.MSG_ID_FIELDS.keys())
                + list(self.custom_persistor_lookup.keys())
            )
        }

    def persist_message_default(self, from_alias: str, payload: SemaType):
        id = None
        id_field = self.MSG_ID_FIELDS.get(payload.type_name)
        if id_field:
            id = getattr(payload, id_field, None)
            if id is None:
                self.logger.warn(f"No data found for {payload.type_name}.{id_field}")
        if not id:
            id = str(uuid.uuid4())

        created_at = None
        created_at_ms_field = self.MSG_CREATED_AT_FIELDS_MS.get(payload.type_name)
        if created_at_ms_field:
            created_at_ms = getattr(payload, created_at_ms_field, None)
            if created_at_ms:
                created_at = datetime.fromtimestamp(created_at_ms / 1000, tz=UTC)
            else:
                self.logger.warn(
                    f"No data found for {payload.type_name}.{created_at_ms_field}"
                )

        created_at_s_field = self.MSG_CREATED_AT_FIELDS_S.get(payload.type_name)
        if created_at_s_field:
            created_at_s = getattr(payload, created_at_s_field, None)
            if created_at_s:
                created_at = datetime.fromtimestamp(created_at_s, tz=UTC)
            else:
                self.logger.warn(
                    f"No data found for {payload.type_name}.{created_at_s_field}"
                )

        return MessagePersistenceInfo(id=id, created_at=created_at)

    def persist_message(
        self, from_alias: str, time_received: datetime, payload: SemaType
    ):
        self.logger.debug(
            f"persisting message of type {payload.type_name}:{payload.version} from {from_alias} at {time_received.isoformat()}"
        )

        persist_fn: Callable[[str, SemaType], MessagePersistenceInfo] | None = None
        custom_persistor = self.custom_persistor_lookup.get(payload.type_name, None)
        if custom_persistor is None:
            persist_fn = self.persist_message_default
        else:
            method_name = f"persist_v{payload.version}"
            persist_fn = getattr(
                custom_persistor, method_name, self.persist_message_default
            )

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

            stmt = insert(MessageSql).on_conflict_do_nothing(
                index_elements=["timestamp", "id"]
            )
            db.execute(stmt, [msg.__dict__])

            # TODO determine if the insert actually inserted anything so we can warn on a duplicate message

            if persistence_info.additional_db_operations is not None:
                persistence_info.additional_db_operations(db)
