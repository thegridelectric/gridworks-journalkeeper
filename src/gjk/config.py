"""Settings for a GridWorks JournalKeeper, readable from environment and/or from env files."""

from gwbase.config import ServiceSettings
from gwbase.transport_format import LeftRightDot
from pydantic import BaseModel, ConfigDict, SecretStr

DEFAULT_ENV_FILE = ".env"


class AwsClient(BaseModel):
    """Settings for interacting with Aws"""

    profile_name: str = "default"
    region_name: str = "us-east-1"
    hosted_zone_id: SecretStr = SecretStr("")
    bucket_name: str = "gwdev"


class Settings(ServiceSettings):
    # The gridworks-data local container under its dev convention
    # (password = role name). Production comes from .env.
    db_url: SecretStr = SecretStr(
        "postgresql+psycopg2://gw_journalkeeper:gw_journalkeeper@localhost:5433/tsdb"
    )
    aws: AwsClient = AwsClient()
    # gwbase-native tap identity (replaces the old g_node_alias hack). JK is
    # not a GNode, so it carries no g_node_id / world_instance_alias / g-node
    # file. GJK_SERVICE_ALIAS overrides the default.
    service_alias: LeftRightDot = "d1.journal"
    service_name: str = "journalkeeper"  # XDG path segment for logs/state
    my_fqdn: str = "localhost"

    model_config = ConfigDict(
        env_prefix="GJK_",
        env_nested_delimiter="__",
        extra="ignore",
    )
