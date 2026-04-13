import json
import logging
import sys
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import dotenv
from sema.runtime import SemaCodec
from sema.runtime.base import DegradedSemaType

from gjk.config import Settings

MSG_TYPES_TO_PARSE = [
    "layout.lite",
    "report.event",
]

ALL_MSG_TYPES = [
    "",
    "layout.lite",
    "report.event",
    "bid",
    "atn.bid",
    "scada.params",
    "flo.next.hour.plans",
    "gridworks.ack",
    "flo.params.house0",
    "gridworks.ping",
    "slow.contract.heartbeat",
    "snapshot.spaceheat",
    "power.watts",
    "glitch",
    "heating.forecast",
    "weather.forecast",
    "gridworks.event.comm.mqtt.connect",
    "gridworks.event.comm.mqtt.disconnect",
    "gridworks.event.comm.mqtt.fully.subscribed",
    "gridworks.event.comm.peer.active",
    "gridworks.event.comm.response.timeout",
    "gridworks.event.problem",
    "weather",
    "new.command.tree",
    "send.snap",
    "gridworks.event.shutdown",
    "gridworks.event.startup",
    "send.layout",
    "no.new.contract.warning",
]


class S3MessageInfo:
    def __init__(self, key_str: str):
        self.key_str = key_str
        [self.from_alias, self.msg_type_name, message_persisted_ms_str, self.source] = (
            key_str.split("/")[-1].split("-")
        )
        self.persist_time = datetime.fromtimestamp(int(message_persisted_ms_str) / 1000)


class S3MessageImporter:
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"
        self.logger = logger

    def find_messages_on_dates(self, dts: list[datetime]) -> Iterable[S3MessageInfo]:
        for dt in dts:
            yield from self.find_messages_on_date(dt)

    def find_messages_in_date_range(
        self, start: datetime, end: datetime
    ) -> Iterable[S3MessageInfo]:
        dt = start
        while dt > end:
            yield from self.find_messages_on_date(dt)
            dt = dt - timedelta(days=1)

    def find_messages_on_date(self, dt: datetime) -> Iterable[S3MessageInfo]:
        prefix = f'{self.world_instance_name}/eventstore/{dt.strftime("%Y%m%d")}'
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.aws_bucket_name, Prefix=prefix)

        date_results = []
        for page in pages:
            for s3_object in page["Contents"]:
                key_str = s3_object["Key"]
                try:
                    msg_info = S3MessageInfo(key_str)
                    if msg_info.msg_type_name in MSG_TYPES_TO_PARSE:
                        date_results.append(msg_info)
                    elif msg_info.msg_type_name not in ALL_MSG_TYPES:
                        self.logger.warning(
                            f'Unknown message type "{msg_info.msg_type_name}" in {key_str}'
                        )
                except Exception as e:
                    self.logger.warning(f"Failed file name parsing for {key_str}")
                    self.logger.exception(e)

        date_results.sort(key=lambda x: x.persist_time, reverse=True)
        yield from date_results
        self.logger.debug(f"Completed messages for {dt.isoformat()}")

        # date_list = self.get_date_folder_list(start_s, duration_hrs)

        # blist = self.get_single_asset_filenames(start_s, duration_hrs, short_alias)

    def download_message(self, msg_info: S3MessageInfo):
        s3_object = self.s3.get_object(
            Bucket=self.aws_bucket_name, Key=msg_info.key_str
        )
        return (s3_object["Body"].read(), s3_object["ContentLength"])


codec = SemaCodec()


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

    settings = Settings(_env_file=dotenv.find_dotenv())
    importer = S3MessageImporter(settings, logger)
    msg_infos = importer.find_messages_in_date_range(
        start=datetime(2026, 2, 19),
        end=datetime(2026, 1, 9),
    )

    # msg_infos = importer.find_messages_on_dates([
    #     datetime(2026, 4, 1),
    #     datetime(2026, 3, 1),
    #     datetime(2026, 2, 1),
    #     # datetime(2026, 1, 1),
    # ])

    # msg_infos = [S3MessageInfo(x) for x in [
    #     'hw1__1/eventstore/20260220/hw1.isone.me.versant.keene.beech.scada-layout.lite-1771564266449-ear.electricity.works.json'
    # ]]

    gb_counter = 0
    byte_counter = 0
    msg_counter = 0
    for msg_info in msg_infos:
        msg_counter += 1
        if byte_counter > 1000000000:
            byte_counter = 0
            gb_counter += 1
            logger.info(
                f"Downloaded ~{gb_counter}GB of data with {msg_counter} messages thru {msg_info.persist_time.isoformat()}"
            )

        if msg_counter % 100 == 0:
            logger.info(
                f"Completed {msg_counter} messages ({byte_counter}B) thru {msg_info.persist_time.isoformat()}"
            )

        try:
            (msg_bytes, msg_length) = importer.download_message(msg_info)
            byte_counter += msg_length
            msg_text = msg_bytes.decode("utf-8")
            msg_dict = json.loads(msg_text)
            sema_obj = codec.from_dict(msg_dict["Payload"], mode="degraded")
            if type(sema_obj) is DegradedSemaType:
                logger.warning(
                    f"Parsed into degraded SEMA type {sema_obj.type_name} (v{sema_obj.version}) from {msg_info.key_str}"
                )
                logger.debug(msg_text)
            else:
                logger.debug(
                    f"Successfully parsed {sema_obj.type_name} (v{sema_obj.version}) from {msg_info.key_str} (persisted at {msg_info.persist_time.isoformat()})"
                )
        except Exception as e:
            logger.error(f"Parsing failure for {msg_info.key_str}: {repr(e)}")
            logger.debug(msg_text)
            return


def parse_file(filename):
    file_bytes = Path(filename).read_bytes()
    return codec.from_bytes(file_bytes)


if __name__ == "__main__":
    main()
