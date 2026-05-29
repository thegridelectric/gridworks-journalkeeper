import uuid
from datetime import UTC, datetime

from gw_data.db.models import ReadingChannelSql, ReadingSql
from sqlalchemy import func, literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
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
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "flo.params.house0"

    def insert_lmp_reading(
        self, db: Session, terminal_asset_alias: str, timestamp: datetime, lmp: float
    ):
        channel_cte = (
            pg_insert(ReadingChannelSql)
            .values(
                id=uuid.uuid4(),
                name="lmp-usd-per-mwh",
                terminal_asset_alias=terminal_asset_alias,
                display_name="$/MWh x100",
                unit="DollarsX100",
                unit_type="gw1.unit",
                channel_type="gjk.pseudo.flo.params.house0",
            )
            .on_conflict_do_update(
                constraint="unique_name_terminal_asset_deactivated_date",
                set_={"deactivated_date": None},
            )
            .returning(ReadingChannelSql.id)
            .cte("channel")
        )

        db.execute(
            pg_insert(ReadingSql)
            .from_select(
                ["channel_id", "message_id", "timestamp", "value"],
                select(
                    channel_cte.c.id,
                    literal(uuid.uuid4()),
                    literal(timestamp),
                    literal(round(lmp * 1000)),
                ),
            )
            .on_conflict_do_nothing()
        )

    def insert_total_price_reading(
        self,
        db: Session,
        terminal_asset_alias: str,
        timestamp: datetime,
        total_price: float,
    ):
        channel_cte = (
            pg_insert(ReadingChannelSql)
            .values(
                id=uuid.uuid4(),
                name="total-usd-per-mwh",
                terminal_asset_alias=terminal_asset_alias,
                display_name="$/MWh x100",
                unit="DollarsX100",
                unit_type="gw1.unit",
                channel_type="gjk.pseudo.flo.params.house0",
            )
            .on_conflict_do_update(
                constraint="unique_name_terminal_asset_deactivated_date",
                set_={"deactivated_date": None},
            )
            .returning(ReadingChannelSql.id)
            .cte("channel")
        )

        db.execute(
            pg_insert(ReadingSql)
            .from_select(
                ["channel_id", "message_id", "timestamp", "value"],
                select(
                    channel_cte.c.id,
                    literal(uuid.uuid4()),
                    literal(timestamp),
                    literal(round(total_price * 1000)),
                ),
            )
            .on_conflict_do_nothing()
        )

    def add_price_readings(
        self, db: Session, from_alias: str, floParams: FloParamsType
    ):
        terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"
        timestamp = datetime.fromtimestamp(floParams.start_unix_s, tz=UTC)

        if floParams.lmp_forecast:
            self.insert_lmp_reading(
                db, terminal_asset_alias, timestamp, floParams.lmp_forecast[0]
            )
            if floParams.dist_price_forecast:
                self.insert_total_price_reading(
                    db,
                    terminal_asset_alias,
                    timestamp,
                    floParams.lmp_forecast[0] + floParams.dist_price_forecast[0],
                )

    def persist(self, from_alias: str, floParams: FloParamsType):
        return MessagePersistenceInfo(
            id=str(uuid.uuid4()),
            created_at=datetime.fromtimestamp(floParams.params_generated_s, tz=UTC),
            additional_db_operations=lambda db: self.add_price_readings(
                db, from_alias, floParams
            ),
        )

    def persist_v007(self, from_alias: str, floParams: FloParamsHouse0):
        return self.persist(from_alias, floParams)
