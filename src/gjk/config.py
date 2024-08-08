"""Settings for a GridWorks JournalKeeper, readable from environment and/or from env files."""

from gwbase.config.rabbit_settings import RabbitBrokerClient
from pydantic import SecretStr
from pydantic_settings import BaseSettings

# from gjk.config import RabbitBrokerClient


DEFAULT_ENV_FILE = ".env"


class Settings(BaseSettings):
    rabbit: RabbitBrokerClient = RabbitBrokerClient()
    db_url: SecretStr = SecretStr(
        "postgresql://persister:PASSWD@journaldb.electricity.works/journaldb"
    )
    db_pass: SecretStr = SecretStr("Passwd")

    class Config:
        env_prefix = "gjk_"
        env_nested_delimiter = "__"
        extra = "ignore"
