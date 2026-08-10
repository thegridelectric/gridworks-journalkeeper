import uuid
from datetime import UTC, datetime

from gw_data.db.models import ReadingChannelSql, ReadingSql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo, default_message_id
from gjk.pseudo_channels import (
    ModernLayout,
    PseudoChannel,
    register_pseudo_channel_factory,
)
from gjk.sema.enums import Gw1Unit
from gjk.sema.types.flo_params_house0 import FloParamsHouse0
from gjk.sema.types.old_versions.flo_params_house0_003 import FloParamsHouse0003
from gjk.sema.types.old_versions.flo_params_house0_004 import FloParamsHouse0004
from gjk.sema.types.old_versions.flo_params_house0_005 import FloParamsHouse0005
from gjk.sema.types.old_versions.flo_params_house0_006 import FloParamsHouse0006

FloParamsType = (
    FloParamsHouse0
    | FloParamsHouse0006
    | FloParamsHouse0005
    | FloParamsHouse0004
    | FloParamsHouse0003
)


class FloParamsHouse0Persistor:
    PSEUDO_CHANNELS = [
        PseudoChannel(
            name="buffer-available-kwh",
            display_name="$/MWh x1000",
            unit=Gw1Unit.KilowattHoursX1000,
            unit_type=Gw1Unit.enum_name(),
        ),
        PseudoChannel(
            name="lmp-usd-per-mwh",
            display_name="$/MWh x1000",
            unit=Gw1Unit.DollarsX1000,
            unit_type=Gw1Unit.enum_name(),
        ),
        PseudoChannel(
            name="total-usd-per-mwh",
            display_name="$/MWh x1000",
            unit=Gw1Unit.DollarsX1000,
            unit_type=Gw1Unit.enum_name(),
        ),
    ]

    @classmethod
    def get_pseudo_channels(cls, layout: ModernLayout) -> list[PseudoChannel]:
        return cls.PSEUDO_CHANNELS

    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "flo.params.house0"

    def add_readings(
        self,
        db: Session,
        from_alias: str,
        message_id: uuid.UUID,
        flo_params: FloParamsType,
    ):
        terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"

        db_channels = (
            db
            .query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.deactivated_date.is_(None),
                ReadingChannelSql.terminal_asset_alias == terminal_asset_alias,
                ReadingChannelSql.name.in_([x.name for x in self.PSEUDO_CHANNELS]),
            )
            .all()
        )

        db_channel_ids_by_name = {x.name: x.id for x in db_channels}

        timestamp = datetime.fromtimestamp(flo_params.start_unix_s, tz=UTC)

        reading_values = {
            "buffer-available-kwh": round(flo_params.buffer_available_kwh * 1000)
        }

        if flo_params.lmp_forecast is not None:
            reading_values["lmp-usd-per-mwh"] = round(flo_params.lmp_forecast[0] * 1000)

            if flo_params.dist_price_forecast is not None:
                total_price = (
                    flo_params.lmp_forecast[0] + flo_params.dist_price_forecast[0]
                )
                reading_values["total-usd-per-mwh"] = round(total_price * 1000)

        readings = []
        for name, value in reading_values.items():
            db_channel_id = db_channel_ids_by_name.get(name)
            if db_channel_id:
                readings.append(
                    ReadingSql(
                        channel_id=db_channel_id,
                        message_id=message_id,
                        timestamp=timestamp,
                        value=value,
                    )
                )

        dicts = [r.__dict__ for r in readings]
        if len(dicts) > 0:
            stmt = pg_insert(ReadingSql).on_conflict_do_nothing(
                index_elements=["timestamp", "channel_id"]
            )
            db.execute(stmt, dicts)

    def persist(
        self, from_alias: str, time_received: datetime, floParams: FloParamsType
    ):
        message_id = uuid.UUID(
            default_message_id(from_alias, self.target_message_type, time_received)
        )
        return MessagePersistenceInfo(
            id=str(message_id),
            created_at=datetime.fromtimestamp(floParams.params_generated_s, tz=UTC),
            additional_db_operations=lambda db: self.add_readings(
                db, from_alias, message_id, floParams
            ),
        )

    def persist_v007(
        self, from_alias: str, time_received: datetime, floParams: FloParamsHouse0
    ):
        return self.persist(from_alias, time_received, floParams)


register_pseudo_channel_factory(FloParamsHouse0Persistor.get_pseudo_channels)
