import uuid
from datetime import UTC, datetime

from gw_data.db.models import ReadingChannelSql, ReadingSql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from gjk.message_persistence_info import MessagePersistenceInfo
from gjk.pseudo_channels import PseudoChannel, register_pseudo_channels
from gjk.sema.enums import Gw1Unit
from gjk.sema.types import WeatherForecast


class WeatherForecastPersistor:
    PSEUDO_CHANNELS = [
        PseudoChannel(
            name="forecast-ws",
            display_name="Forecast Wind Speed",
            unit=Gw1Unit.MilesPerHourX1000,
            unit_type=Gw1Unit.enum_name(),
        ),
        PseudoChannel(
            name="forecast-oat",
            display_name="Forecast Outdoor Air Temp",
            unit=Gw1Unit.FahrenheitX100,
            unit_type=Gw1Unit.enum_name(),
        ),
    ]

    @classmethod
    def get_pseudo_channels(cls) -> list[PseudoChannel]:
        return cls.PSEUDO_CHANNELS

    def __init__(self, logger):
        self.logger = logger
        self.target_message_type = "weather.forecast"

    def add_readings(
        self,
        db: Session,
        from_alias: str,
        message_id: uuid.UUID,
        forecast: WeatherForecast,
    ):
        terminal_asset_alias = from_alias.split(".scada")[0] + ".ta"

        db_channels = (
            db.query(ReadingChannelSql)
            .filter(
                ReadingChannelSql.deactivated_date.is_(None),
                ReadingChannelSql.terminal_asset_alias == terminal_asset_alias,
                ReadingChannelSql.name.in_([x.name for x in self.PSEUDO_CHANNELS]),
            )
            .all()
        )

        db_channel_ids_by_name = {x.name: x.id for x in db_channels}

        timestamp = datetime.fromtimestamp(forecast.time[0], tz=UTC)

        reading_values = {
            "forecast-ws": round(forecast.wind_speed_mph[0] * 1000),
            "forecast-oat": round(forecast.oat_f[0] * 1000),
        }

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

    def persist_v000(self, from_alias: str, forecast: WeatherForecast):
        message_id = uuid.uuid4()
        return MessagePersistenceInfo(
            id=str(message_id),
            created_at=datetime.fromtimestamp(forecast.forecast_created_s, tz=UTC),
            additional_db_operations=lambda db: self.add_readings(
                db, from_alias, message_id, forecast
            ),
        )


register_pseudo_channels(WeatherForecastPersistor.get_pseudo_channels())
