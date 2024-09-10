########################################
# SAMPLE SMALL GROUP UPDATE
########################################
import dotenv
import pendulum
from gjk.config import Settings
from gjk.models import DataChannelSql, NodalHourlyEnergySql
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import Session, sessionmaker

settings = Settings(_env_file=dotenv.find_dotenv())
engine = create_engine(settings.db_url.get_secret_value())
Session = sessionmaker(bind=engine)
session = Session()


dcs = session.query(DataChannelSql).all()
# Define the names to update
names_to_update = ["hp-idu-pwr", "hp-odu-pwr"]


#  Update the in_power_metering field to True for the specified names
session.query(DataChannelSql).filter(DataChannelSql.name.in_(names_to_update)).update({
    "in_power_metering": True
})

# Commit the transaction
session.commit()

dc = dcs[0]


# Pick Nodal hourly energies in Feb for hp-odu, greater than 0
tz = "America/New_York"
feb_start = pendulum.datetime(2024, 2, 1, tz=tz).int_timestamp
feb_end = pendulum.datetime(2024, 3, 1, tz=tz).int_timestamp

result = (
    session.query(NodalHourlyEnergySql)
    .join(DataChannelSql, NodalHourlyEnergySql.power_channel_id == DataChannelSql.id)
    .filter(
        and_(
            NodalHourlyEnergySql.hour_start_s.between(feb_start, feb_end),
            NodalHourlyEnergySql.watt_hours > 0,
            DataChannelSql.name.ilike("%hp-odu%"),
        )
    )
    .all()
)
