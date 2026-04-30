import uuid
from datetime import datetime

from gw_data.db.models import ReadingChannelSql
from sema.runtime.enums import SpaceheatTelemetryName
from sema.runtime.enums.old_versions.gw1_unit_000 import Gw1Unit000
from sema.runtime.types import DataChannelGt, DerivedChannelGt, LayoutLite
from sema.runtime.types.old_versions.data_channel_gt_001 import DataChannelGt001
from sema.runtime.types.old_versions.derived_channel_gt_000 import DerivedChannelGt000
from sema.runtime.types.old_versions.derived_channel_gt_001 import DerivedChannelGt001
from sema.runtime.types.old_versions.layout_lite_007 import LayoutLite007
from sema.runtime.types.old_versions.layout_lite_008 import LayoutLite008
from sema.runtime.types.old_versions.layout_lite_009 import LayoutLite009
from sema.runtime.types.old_versions.layout_lite_010 import LayoutLite010
from sema.runtime.types.old_versions.layout_lite_011 import LayoutLite011
from sema.runtime.types.old_versions.layout_lite_012 import LayoutLite012
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.synthetic_channels import ALL_SYNTHETIC_CHANNELS, SyntheticChannel


class LayoutLitePersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "layout.lite"

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
        from_terminal_asset_alias: str,
    ) -> list[ReadingChannelSql]:
        return [
            x.to_db_channel(from_terminal_asset_alias) for x in ALL_SYNTHETIC_CHANNELS
        ]

    def sync_reading_channels(
        self,
        db: Session,
        from_alias: str,
        layout: LayoutLite
        | LayoutLite012
        | LayoutLite011
        | LayoutLite010
        | LayoutLite009
        | LayoutLite008
        | LayoutLite007,
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

        for sc in self.generate_synthetic_db_channels(from_terminal_asset_alias):
            db_channel = db_channels_by_name_to_sync.get(sc.name)
            if db_channel is None:
                new_db_channels.append(sc)
            else:
                if (
                    db_channel.unit != sc.unit
                    or db_channel.unit_type != Gw1Unit000.enum_name()
                    or db_channel.channel_type != SyntheticChannel.CHANNEL_TYPE
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

    def persist_v007(self, from_alias: str, layout: LayoutLite007):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v008(self, from_alias: str, layout: LayoutLite008):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v009(self, from_alias: str, layout: LayoutLite009):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v010(self, from_alias: str, layout: LayoutLite010):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v011(self, from_alias: str, layout: LayoutLite011):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v012(self, from_alias: str, layout: LayoutLite012):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v013(self, from_alias: str, layout: LayoutLite):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )
