import logging
import sys
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import List

import dotenv
from gw_data.db.models import MessageSql, ReadingChannelSql
from sema.runtime import SemaCodec, SemaType
from sema.runtime.enums import SpaceheatTelemetryName
from sema.runtime.enums.old_versions.gw1_unit_000 import Gw1Unit000
from sema.runtime.property_format import UUID4Str
from sema.runtime.types import DataChannelGt, DerivedChannelGt, LayoutLite
from sema.runtime.types.old_versions.data_channel_gt_001 import DataChannelGt001
from sema.runtime.types.old_versions.derived_channel_gt_000 import DerivedChannelGt000
from sema.runtime.types.old_versions.derived_channel_gt_001 import DerivedChannelGt001
from sema.runtime.types.old_versions.layout_lite_009 import LayoutLite009
from sema.runtime.types.old_versions.layout_lite_010 import LayoutLite010
from sema.runtime.types.old_versions.layout_lite_011 import LayoutLite011
from sema.runtime.types.old_versions.layout_lite_012 import LayoutLite012
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.config import Settings


@dataclass
class MessagePersistenceInfo:
    id: UUID4Str
    created_at: datetime
    additional_db_operations: Callable[[Session], None]


SYNTHETIC_CHANNEL_TYPE = "gjk.synthetic"


class SemaMessagePersistor:
    def __init__(self, settings: Settings, codec: SemaCodec, logger):
        self.settings = settings
        self.codec = codec
        engine = create_engine(settings.db_url.get_secret_value(), echo=False)
        self.Session = sessionmaker(bind=engine)
        self.logger = logger

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

    def persist_message(
        self, from_alias: str, time_received: datetime, payload: SemaType
    ):
        self.logger.debug(
            f"persisting message of type {payload.type_name}:{payload.version} from {from_alias} at {time_received.isoformat()}"
        )

        method_name = (
            f'process_{payload.type_name.replace(".", "_")}_v{payload.version}'
        )
        process_fn = getattr(self, method_name)
        if process_fn:
            persistence_info: MessagePersistenceInfo = process_fn(from_alias, payload)
            with self.get_db() as db:
                msg = MessageSql(
                    id=uuid.UUID(persistence_info.id),
                    timestamp=persistence_info.created_at
                    if persistence_info.created_at
                    else time_received,
                    created_at=persistence_info.created_at,
                    persisted_at=time_received,
                    from_alias=from_alias,
                    message_type_name=payload.type_name,
                    payload=payload.to_dict(),
                )
                db.add(msg)
                persistence_info.additional_db_operations(db)

    def data_channel_to_db(
        self, dc: DataChannelGt | DataChannelGt001
    ) -> ReadingChannelSql:
        return ReadingChannelSql(
            id=uuid.uuid4(),
            name=dc.name,
            terminal_asset_alias=dc.terminal_asset_alias,
            display_name=dc.display_name,
            unit=dc.telemetry_name,
            unit_type=SpaceheatTelemetryName.enum_name(),
            channel_type=DataChannelGt.type_name_value(),
        )

    def derived_channel_to_db(
        self, dc: DerivedChannelGt001 | DerivedChannelGt000
    ) -> ReadingChannelSql:
        return ReadingChannelSql(
            id=uuid.uuid4(),
            name=dc.name,
            terminal_asset_alias=dc.terminal_asset_alias,
            display_name=dc.display_name,
            unit=dc.output_unit if dc.output_unit is not None else "Unknown",
            unit_type=Gw1Unit000.enum_name(),
            channel_type=DerivedChannelGt.type_name_value(),
        )

    def generate_synthetic_db_channels(
        self,
        layout: LayoutLite
        | LayoutLite012
        | LayoutLite011
        | LayoutLite010
        | LayoutLite009,
    ) -> list[ReadingChannelSql]:
        # TODO
        return []

    def sync_reading_channels(
        self,
        db: Session,
        from_alias: str,
        layout: LayoutLite
        | LayoutLite012
        | LayoutLite011
        | LayoutLite010
        | LayoutLite009,
    ):
        from_terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"
        db_channels = (
            db.query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.deactivated_date.is_(None),
                ReadingChannelSql.terminal_asset_alias == from_terminal_asset_alias,
            )
            .all()
        )
        db_channels_by_name_to_sync = {c.name: c for c in db_channels}

        new_db_channels = []

        msg_timestamp = datetime.fromtimestamp(layout.message_created_ms / 1000)

        # Look at every channel (data, derived, and synthetic)
        #   If it does not exist in the database, add it
        #   If it exists with a different unit or unit type, add a new one (do we need to deactivate it?)
        #   If it exists in the database with the same unit and unit type, reactivate it if necessary
        for dc in layout.data_channels:
            db_channel = db_channels_by_name_to_sync.get(dc.name)
            if db_channel is None:
                new_db_channels.append(self.data_channel_to_db(dc))
            else:
                if (
                    db_channel.unit != dc.telemetry_name
                    or db_channel.unit_type != SpaceheatTelemetryName.enum_name()
                    or db_channel.channel_type != DataChannelGt.type_name_value()
                ):
                    self.logger.info(
                        f"Found data channel {dc.name} for {dc.terminal_asset_alias} with mismatched unit/type in DB: {db_channel.channel_type}:{db_channel.unit_type}:{db_channel.unit}/{dc.telemetry_name}"
                    )
                    new_db_channels.append(self.data_channel_to_db(dc))
                    db_channel.deactivated_date = msg_timestamp

                del db_channels_by_name_to_sync[dc.name]

        for dc in layout.derived_channels:
            db_channel = db_channels_by_name_to_sync.get(dc.name)
            if db_channel is None:
                new_db_channels.append(self.derived_channel_to_db(dc))
            else:
                if (
                    db_channel.unit != dc.output_unit
                    or db_channel.unit_type != Gw1Unit000.enum_name()
                    or db_channel.channel_type != DerivedChannelGt.type_name_value()
                ):
                    self.logger.info(
                        f"Found derived channel {dc.name} for {dc.terminal_asset_alias} with mismatched unit/type in DB: {db_channel.channel_type}:{db_channel.unit_type}:{db_channel.unit}/{dc.output_unit}"
                    )
                    new_db_channels.append(self.derived_channel_to_db(dc))
                    db_channel.deactivated_date = msg_timestamp

                del db_channels_by_name_to_sync[dc.name]

        for sc in self.generate_synthetic_db_channels(layout):
            db_channel = db_channels_by_name_to_sync.get(sc.name)
            if db_channel is None:
                new_db_channels.append(sc)
            else:
                if (
                    db_channel.unit != sc.unit
                    or db_channel.unit_type != Gw1Unit000.enum_name()
                    or db_channel.channel_type != SYNTHETIC_CHANNEL_TYPE
                ):
                    self.logger.info(
                        f"Found synthetic channel {sc.name} for {sc} with mismatched unit/type in DB: {db_channel.channel_type}:{db_channel.unit_type}:{db_channel.unit}/{sc.output_unit}"
                    )
                    new_db_channels.append(sc)
                    db_channel.deactivated_date = msg_timestamp

                del db_channels_by_name_to_sync[sc.name]

        for db_only_channel in db_channels_by_name_to_sync.values():
            self.logger.info(
                f"Data channel {db_only_channel.name} for {db_only_channel.terminal_asset_alias} exists only in the database"
            )
            db_only_channel.deactivated_date = msg_timestamp

        for ch in new_db_channels:
            db.add(ch)

    def process_layout_lite_v009(self, from_alias: str, layout: LayoutLite009):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def process_layout_lite_v010(self, from_alias: str, layout: LayoutLite010):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def process_layout_lite_v011(self, from_alias: str, layout: LayoutLite011):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def process_layout_lite_v012(self, from_alias: str, layout: LayoutLite012):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def process_layout_lite_v013(self, from_alias: str, layout: LayoutLite):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )


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
