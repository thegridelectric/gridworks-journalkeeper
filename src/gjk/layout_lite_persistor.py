import uuid
from datetime import UTC, datetime

from gw_data.db.models import ReadingChannelSql
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.pseudo_channels import ModernLayout, PseudoChannel, get_pseudo_channels
from gjk.sema.enums import Gw1Unit, SpaceheatTelemetryName
from gjk.sema.types import DataChannelGt, DerivedChannelGt, LayoutLite
from gjk.sema.types.old_versions.data_channel_gt_001 import DataChannelGt001
from gjk.sema.types.old_versions.derived_channel_gt_000 import DerivedChannelGt000
from gjk.sema.types.old_versions.layout_lite_007 import LayoutLite007
from gjk.sema.types.old_versions.layout_lite_008 import LayoutLite008
from gjk.sema.types.old_versions.layout_lite_009 import LayoutLite009
from gjk.sema.types.old_versions.layout_lite_010 import LayoutLite010
from gjk.sema.types.old_versions.layout_lite_011 import LayoutLite011
from gjk.sema.types.old_versions.layout_lite_012 import LayoutLite012


class LayoutLitePersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "layout.lite"

    class ReadingChannelSyncProcess:
        def __init__(
            self, logger, db: Session, layout: ModernLayout, terminal_asset_alias: str
        ):
            self.logger = logger
            self.db = db
            self.layout = layout
            self.msg_timestamp = datetime.fromtimestamp(
                layout.message_created_ms / 1000, UTC
            )
            self.terminal_asset_alias = terminal_asset_alias

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
            self, dc: DerivedChannelGt | DerivedChannelGt000
        ) -> ReadingChannelSql:
            return ReadingChannelSql(
                id=uuid.uuid4(),
                name=dc.name,
                terminal_asset_alias=dc.terminal_asset_alias,
                display_name=dc.display_name,
                unit=dc.output_unit if dc.output_unit is not None else "Unknown",
                unit_type=Gw1Unit.enum_name(),
                channel_type=DerivedChannelGt.type_name_value(),
            )

        def pseudo_channel_to_db(self, pc: PseudoChannel) -> ReadingChannelSql:
            return ReadingChannelSql(
                id=uuid.uuid4(),
                name=pc.name,
                terminal_asset_alias=self.terminal_asset_alias,
                display_name=pc.display_name,
                unit=pc.unit,
                unit_type=pc.unit_type,
                channel_type=PseudoChannel.CHANNEL_TYPE,
            )

        def sync_data_channels(self):
            for dc in self.layout.data_channels:
                db_channel = self.existing_db_channels_by_name.get(dc.name)
                if db_channel is None:
                    self.new_db_channels.append(self.data_channel_to_db(dc))
                else:
                    if (
                        db_channel.unit != dc.telemetry_name
                        or db_channel.unit_type != SpaceheatTelemetryName.enum_name()
                        or db_channel.channel_type != DataChannelGt.type_name_value()
                    ):
                        self.logger.info(
                            f"Found data channel {dc.name} for {dc.terminal_asset_alias} with mismatched unit/type in DB: {db_channel.channel_type}:{db_channel.unit_type}:{db_channel.unit}/{dc.telemetry_name}"
                        )
                        self.new_db_channels.append(self.data_channel_to_db(dc))
                        db_channel.deactivated_date = self.msg_timestamp

                    del self.existing_db_channels_by_name[dc.name]

        def sync_derived_channels(self):
            for dc in self.layout.derived_channels:
                db_channel = self.existing_db_channels_by_name.get(dc.name)
                if db_channel is None:
                    self.new_db_channels.append(self.derived_channel_to_db(dc))
                else:
                    if (
                        db_channel.unit != dc.output_unit
                        or db_channel.unit_type != Gw1Unit.enum_name()
                        or db_channel.channel_type != DerivedChannelGt.type_name_value()
                    ):
                        self.logger.info(
                            f"Found derived channel {dc.name} for {dc.terminal_asset_alias} with mismatched unit/type in DB: {db_channel.channel_type}:{db_channel.unit_type}:{db_channel.unit}/{dc.output_unit}"
                        )
                        self.new_db_channels.append(self.derived_channel_to_db(dc))
                        db_channel.deactivated_date = self.msg_timestamp

                    del self.existing_db_channels_by_name[dc.name]

        def sync_pseudo_channels(self):
            for pc in get_pseudo_channels(self.layout):
                db_channel = self.existing_db_channels_by_name.get(pc.name)
                if db_channel is None:
                    self.new_db_channels.append(self.pseudo_channel_to_db(pc))
                else:
                    if (
                        db_channel.unit != pc.unit
                        or db_channel.unit_type != pc.unit_type
                        or db_channel.channel_type != PseudoChannel.CHANNEL_TYPE
                    ):
                        self.logger.info(
                            f"Found pseudo channel {pc.name} for {pc} with mismatched unit/type in DB: {db_channel.channel_type}:{db_channel.unit_type}:{db_channel.unit}/{pc.unit_type}:{pc.unit}"
                        )
                        self.new_db_channels.append(self.pseudo_channel_to_db(pc))
                        db_channel.deactivated_date = self.msg_timestamp

                    del self.existing_db_channels_by_name[pc.name]

        def execute(self):
            db_channels = (
                self.db.query(ReadingChannelSql)
                .filter(
                    ReadingChannelSql.deactivated_date.is_(None),
                    ReadingChannelSql.terminal_asset_alias == self.terminal_asset_alias,
                )
                .all()
            )
            self.existing_db_channels_by_name = {c.name: c for c in db_channels}

            self.new_db_channels = []

            # Look at every channel (data, derived, and pseudo)
            #   If it does not exist as active in the database, add it
            #   If it exists with a different unit or unit type, deactivated it and add a new one

            self.sync_data_channels()
            self.sync_derived_channels()
            self.sync_pseudo_channels()

            for db_only_channel in self.existing_db_channels_by_name.values():
                self.logger.info(
                    f"Data channel {db_only_channel.name} for {db_only_channel.terminal_asset_alias} exists only in the database"
                )
                db_only_channel.deactivated_date = self.msg_timestamp

            for ch in self.new_db_channels:
                self.db.add(ch)

    def sync_reading_channels(
        self,
        db: Session,
        from_alias: str,
        layout: ModernLayout,
    ):
        self.ReadingChannelSyncProcess(
            self.logger, db, layout, from_alias.split(".scada")[0] + ".ta"
        ).execute()

    def persist(self, from_alias: str, layout: ModernLayout):
        return MessagePersistenceInfo(
            id=layout.message_id,
            created_at=datetime.fromtimestamp(layout.message_created_ms / 1000, tz=UTC),
            additional_db_operations=lambda db: self.sync_reading_channels(
                db, from_alias, layout
            ),
        )

    def persist_v007(
        self, from_alias: str, time_received: datetime, layout: LayoutLite007
    ):
        return self.persist(from_alias, layout)

    def persist_v008(
        self, from_alias: str, time_received: datetime, layout: LayoutLite008
    ):
        return self.persist(from_alias, layout)

    def persist_v009(
        self, from_alias: str, time_received: datetime, layout: LayoutLite009
    ):
        return self.persist(from_alias, layout)

    def persist_v010(
        self, from_alias: str, time_received: datetime, layout: LayoutLite010
    ):
        return self.persist(from_alias, layout)

    def persist_v011(
        self, from_alias: str, time_received: datetime, layout: LayoutLite011
    ):
        return self.persist(from_alias, layout)

    def persist_v012(
        self, from_alias: str, time_received: datetime, layout: LayoutLite012
    ):
        return self.persist(from_alias, layout)

    def persist_v013(
        self, from_alias: str, time_received: datetime, layout: LayoutLite
    ):
        return self.persist(from_alias, layout)
