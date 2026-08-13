import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

from gw_data.db.models import MessageSql
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from gjk.config import Settings
from gjk.flo_params_house0_persistor import FloParamsHouse0Persistor
from gjk.layout_lite_persistor import LayoutLitePersistor
from gjk.message_persistence_info import (
    MESSAGE_ID_NAMESPACE,
    MessagePersistenceInfo,
    default_message_id,
)
from gjk.report_event_persistor import ReportEventPersistor
from gjk.sema import SemaCodec, SemaType
from gjk.g_node_forest_persistor import GNodeForestPersistor
from gjk.weather_bundle_persistor import WeatherBundlePersistor
from gjk.weather_forecast_persistor import WeatherForecastPersistor

# Re-exported from message_persistence_info so existing importers (and tests)
# can keep importing MESSAGE_ID_NAMESPACE from here.
__all__ = ["MESSAGE_ID_NAMESPACE", "SemaMessagePersistor"]


class SemaMessagePersistor:
    MSG_CREATED_AT_FIELDS_MS = {
        "glitch": "created_ms",
        "gridworks.event.problem": "time_created_ms",
        "energy.instruction": "send_time_ms",
        "gw.weather.forecast": "message_created_ms",
        "new.command.tree": "unix_ms",
        "snapshot.spaceheat": "snapshot_time_unix_ms",
        "scada.params": "unix_time_ms",
        "ticklist.reed.report": "scada_received_unix_ms",
        "ticklist.hall.report": "scada_received_unix_ms",
        # Obsolete message types
        "report": "message_created_ms",
    }

    MSG_CREATED_AT_FIELDS_S = {
        "heating.forecast": "forecast_created_s",
    }

    MSG_ID_FIELDS = {
        "gridworks.event.problem": "message_id",
        "scada.params": "message_id",
        # Weather records are durable identities; their own uuid is the
        # message id, so a record replayed through the bus dedupes. (The
        # bundle is absent here: WeatherBundlePersistor owns it, keeping
        # the same natural-id rule.)
        "gw.weather.channel.gt": "id",
        "gw.weather.forecast.channel.gt": "id",
        "gw.weather.location.gt": "id",
        # Obsolete message types
        "report": "id",
    }

    # Messages with no id or created_at info, but we still want to persist
    BASIC_MSG_TYPES = [
        "atn.bid",
        # The observation carries ObservationTime (the station's claim
        # time, ISO seconds) but no message-created field by design;
        # readings projection will key on ObservationTime later.
        "gw.weather.observation",
        # The create round: the journal carries every minting act, not
        # only the eventstore. CommandHash is a sha256 hex, not a uuid,
        # so the id stays the deterministic uuid5 default.
        "gw.weather.cmd.ack",
        "gw.weather.cmd.nack",
        "gw.weather.create.cmd",
        "latest.price",
        "power.watts",
    ]

    def __init__(
        self, settings: Settings, codec: SemaCodec, logger, db_echo: bool = False
    ):
        self.settings = settings
        self.codec = codec
        engine = create_engine(settings.db_url.get_secret_value(), echo=db_echo)
        self.Session = sessionmaker(bind=engine)
        self.logger = logger

        self.custom_persistor_lookup = {
            x.target_message_type: x
            for x in [
                LayoutLitePersistor(logger),
                ReportEventPersistor(logger),
                FloParamsHouse0Persistor(logger),
                WeatherForecastPersistor(logger),
                WeatherBundlePersistor(logger),
                # The registry alias is the universe's `<universe>.gnr` —
                # derived from this service's own alias, never a second
                # literal that can drift.
                GNodeForestPersistor(
                    logger,
                    registry_alias=(f"{settings.service_alias.split('.')[0]}.gnr"),
                ),
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

    def persist_message_default(
        self, from_alias: str, payload: SemaType, time_received: datetime
    ):
        id = None
        id_field = self.MSG_ID_FIELDS.get(payload.type_name)
        if id_field:
            id = getattr(payload, id_field, None)
            if id is None:
                self.logger.warn(f"No data found for {payload.type_name}.{id_field}")
        if not id:
            id = default_message_id(from_alias, payload.type_name, time_received)

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
        self,
        from_alias: str,
        time_received: datetime,
        payload: SemaType,
        *,
        live: bool,
    ):
        """live: True when the message arrives from the broker (current fleet
        traffic); False when replayed from the persistent store (S3 backfill).
        The raw message is stored either way. A custom persistor that declares
        ``fanout_on_import = False`` projects CURRENT state — its fan-out runs
        only on live messages, so replayed history cannot regress the
        projection."""
        self.logger.debug(
            f"persisting message of type {payload.type_name}:{payload.version} from {from_alias} at {time_received.isoformat()}"
        )

        custom_persistor = self.custom_persistor_lookup.get(payload.type_name, None)
        custom_fn = (
            getattr(custom_persistor, f"persist_v{payload.version}", None)
            if custom_persistor is not None
            else None
        )
        if custom_fn is not None:
            persistence_info = custom_fn(from_alias, time_received, payload)
            if not live and not custom_persistor.fanout_on_import:
                persistence_info.additional_db_operations = None
        else:
            persistence_info = self.persist_message_default(
                from_alias, payload, time_received
            )
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
