"""Settings for a GridWorks Persister, readable from environment and/or from env files."""


from pydantic import SecretStr
from pydantic_settings import BaseSettings

from gwbase.config.rabbit_settings import RabbitBrokerClient 
#from gwbase.config import RabbitBrokerClient


DEFAULT_ENV_FILE = ".env"

class Settings(BaseSettings):
    rabbit: RabbitBrokerClient = RabbitBrokerClient()
    db_url: SecretStr = SecretStr("postgresql+asyncpg://persister:PASSWD@journaldb.electricity.works/journaldb")
    db_pass: SecretStr = SecretStr("Passwd")
    class Config:
        env_prefix = "GWP_"
        env_nested_delimiter = "__"
