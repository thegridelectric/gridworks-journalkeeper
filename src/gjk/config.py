"""Settings for a GridWorks JournalKeeper, readable from environment and/or from env files."""

from gwbase.config import GNodeSettings
from pydantic import BaseModel, ConfigDict, SecretStr

DEFAULT_ENV_FILE = ".env"


class AwsClient(BaseModel):
    """Settings for interacting with Aws"""

    profile_name: str = "default"
    region_name: str = "us-east-1"
    hosted_zone_id: SecretStr = SecretStr("")
    bucket_name: str = "gwdev"


class Settings(GNodeSettings):
    db_url: SecretStr = SecretStr(
        "postgresql://journaldb:PASSWD@journaldb.electricity.works/journaldb"
    )
    gbo_db_url: SecretStr = SecretStr("postgresql://backofficedb:PASSWD@journaldb.electricity.works/backofficedb""")
    aws: AwsClient = AwsClient()
    ops_genie_api_key: SecretStr = SecretStr("OpsGenieAPIKey")
    g_node_alias: str = "d1.journal"
    g_node_id: str = "00000000-0000-0000-0000-000000000000"
    world_instance_alias: str = "d1__1"
    my_fqdn: str = "localhost"
    visualizer_api_password: SecretStr = SecretStr("ThermostatAPIKey")

    model_config = ConfigDict(
        env_prefix="GJK_",
        env_nested_delimiter="__",
        extra="ignore",
    )
