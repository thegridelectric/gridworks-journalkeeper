########################################
# SAMPLE SMALL GROUP UPDATE
########################################
import dotenv
from gjk.config import Settings
from gjk.models import DataChannelSql
from sqlalchemy import create_engine
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
