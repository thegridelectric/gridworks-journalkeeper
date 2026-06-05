import uuid
from datetime import UTC, datetime

from gw_data.db.models import ReadingChannelSql, ReadingSql
from sqlalchemy import literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.sema.enums import Gw1Unit
from gjk.sema.types import WeatherForecast


class WeatherForecastPersistor:
    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "weather.forecast"

    def insert_reading_with_channel(
        self, db: Session, channel: ReadingChannelSql, timestamp: datetime, value: int
    ):
        channel_cte = (
            pg_insert(ReadingChannelSql)
            .values(
                id=channel.id,
                name=channel.name,
                terminal_asset_alias=channel.terminal_asset_alias,
                display_name=channel.display_name,
                unit=channel.unit,
                unit_type=channel.unit_type,
                channel_type="gjk.pseudo.weather.forecast",
            )
            .on_conflict_do_update(
                constraint="unique_name_terminal_asset_deactivated_date",
                set_={"deactivated_date": None},
            )
            .returning(ReadingChannelSql.id)
            .cte("channel")
        )
        return db.execute(
            pg_insert(ReadingSql)
            .from_select(
                ["channel_id", "message_id", "timestamp", "value"],
                select(
                    channel_cte.c.id,
                    literal(uuid.uuid4()),
                    literal(timestamp),
                    literal(value),
                ),
            )
            .on_conflict_do_nothing()
        )

    def add_readings(self, db: Session, from_alias: str, forecast: WeatherForecast):
        terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"

        self.insert_reading_with_channel(
            db,
            ReadingChannelSql(
                id=uuid.uuid4(),
                name="forecast-ws",
                terminal_asset_alias=terminal_asset_alias,
                display_name="Forecast WS",
                unit=Gw1Unit.MilesPerHourX1000,
                unit_type=Gw1Unit.enum_name(),
            ),
            timestamp=datetime.fromtimestamp(forecast.time[0], tz=UTC),
            value=round(forecast.wind_speed_mph[0] * 1000),
        )

        self.insert_reading_with_channel(
            db,
            ReadingChannelSql(
                id=uuid.uuid4(),
                name="forecast-oat",
                terminal_asset_alias=terminal_asset_alias,
                display_name="Forecast Outdoor Air Temp",
                unit=Gw1Unit.FahrenheitX100,
                unit_type=Gw1Unit.enum_name(),
            ),
            timestamp=datetime.fromtimestamp(forecast.time[0], tz=UTC),
            value=round(forecast.oat_f[0] * 1000),
        )

    def persist_v000(self, from_alias: str, forecast: WeatherForecast):
        return MessagePersistenceInfo(
            id=str(uuid.uuid4()),
            created_at=datetime.fromtimestamp(forecast.forecast_created_s, tz=UTC),
            additional_db_operations=lambda db: self.add_readings(
                db, from_alias, forecast
            ),
        )
