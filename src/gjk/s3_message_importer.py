import argparse
import json
import logging
import sys
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Literal

import boto3
import dotenv

from gjk.config import Settings
from gjk.sema import SemaCodec, SemaType
from gjk.sema_message_persistor import SemaMessagePersistor

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
    "ticklist.hall.report",
]


class S3MessageInfo:
    def __init__(self, key_str: str):
        self.key_str = key_str
        [self.from_alias, self.msg_type_name, message_persisted_ms_str, self.source] = (
            key_str.split("/")[-1].split("-")
        )
        self.persist_time = datetime.fromtimestamp(
            int(message_persisted_ms_str) / 1000, tz=UTC
        )


class S3MessageImporter:
    def __init__(self, settings: Settings, msg_types: set[str], logger):
        self.settings = settings
        self.s3 = boto3.client("s3")
        self.aws_bucket_name = "gwdev"
        self.world_instance_name = "hw1__1"
        self.msg_types = msg_types
        self.logger = logger

    def find_messages_on_dates(
        self, dts: list[datetime], sort: Literal["none", "asc", "desc"] = "none"
    ) -> Iterable[S3MessageInfo]:
        for dt in dts:
            yield from self.find_messages_on_date(dt, sort=sort)

    def find_messages_in_date_range(
        self, start: datetime, end: datetime
    ) -> Iterable[S3MessageInfo]:
        dt = start
        if end < start:
            while dt >= end:
                yield from self.find_messages_on_date(dt, sort="desc")
                dt = dt - timedelta(days=1)
        else:
            while dt <= end:
                yield from self.find_messages_on_date(dt, sort="asc")
                dt = dt + timedelta(days=1)

    def find_messages_on_date(
        self,
        dt: datetime,
        skip_past: str | None = None,
        sort: Literal["none", "asc", "desc"] = "none",
    ) -> Iterable[S3MessageInfo]:
        prefix = f'{self.world_instance_name}/eventstore/{dt.strftime("%Y%m%d")}'
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.aws_bucket_name, Prefix=prefix)

        date_results: list[S3MessageInfo] = []
        for page in pages:
            for s3_object in page.get("Contents", []):
                key_str = s3_object["Key"]
                try:
                    msg_info = S3MessageInfo(key_str)
                    if msg_info.msg_type_name in self.msg_types:
                        date_results.append(msg_info)
                    elif msg_info.msg_type_name not in ALL_MSG_TYPES:
                        self.logger.warning(
                            f'Unknown message type "{msg_info.msg_type_name}" in {key_str}'
                        )
                except Exception as e:
                    self.logger.warning(f"Failed file name parsing for {key_str}")
                    self.logger.exception(e)

        if sort != "none":
            date_results.sort(key=lambda x: x.persist_time, reverse=(sort == "desc"))

        if skip_past is not None:
            skip_index = -1
            for i in range(0, len(date_results)):
                if skip_past == date_results[i].key_str:
                    skip_index = i
                    break

            if skip_index >= 0:
                date_results = date_results[skip_index + 1 :]

        yield from date_results
        self.logger.info(f"Completed messages for {dt.isoformat()}")

        # date_list = self.get_date_folder_list(start_s, duration_hrs)

        # blist = self.get_single_asset_filenames(start_s, duration_hrs, short_alias)

    def download_message(self, msg_info: S3MessageInfo):
        s3_object = self.s3.get_object(
            Bucket=self.aws_bucket_name, Key=msg_info.key_str
        )
        return (s3_object["Body"].read(), s3_object["ContentLength"])


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def main(argv=None):
    # argv=None -> sys.argv[1:] (unchanged CLI behavior); tests pass an explicit
    # list so pytest's own args never leak into this parser.
    parser = argparse.ArgumentParser(
        description="Import messages from S3 into the database"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Include debug logging to stdout"
    )
    parser.add_argument("--db-echo", action="store_true", help="Echo SQL to stdout")
    parser.add_argument(
        "--abort-on-error",
        action="store_true",
        help="Abort on failed messages instead of skipping",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If true, downloads and parses messages but does not store them",
    )
    parser.add_argument(
        "--message-path", type=str, help="S3 key path of a single message to process"
    )
    parser.add_argument("--start", type=_parse_date, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=_parse_date, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--message-types",
        type=str,
        help="When importing a date range, a comma-separated list of message types to import -- or, when preceded with '~', a list of message types to skip",
    )
    args = parser.parse_args(argv)

    if args.message_path is None and (args.start is None or args.end is None):
        parser.error("--start and --end are required unless --message-path is provided")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(stderr_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel("DEBUG" if args.verbose else "INFO")
    stdout_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(stdout_handler)

    settings = Settings(
        service_alias="gjk.s3import",
        _env_file=dotenv.find_dotenv(),  # type: ignore
    )

    codec = SemaCodec()
    msg_persistor = SemaMessagePersistor(settings, codec, logger, db_echo=args.db_echo)

    if args.message_path is not None:
        importer = S3MessageImporter(
            settings, msg_persistor.all_known_message_types(), logger
        )
        msg_infos: Iterable[S3MessageInfo] = [S3MessageInfo(args.message_path)]
    else:
        # args.message_types is None when the flag is omitted (str() would turn
        # that into the truthy "None" and silently import nothing).
        message_types_arg = args.message_types
        if message_types_arg:
            if message_types_arg.startswith("~"):
                msg_types = msg_persistor.all_known_message_types()
                for msg_type in message_types_arg[1:].split(","):
                    msg_types.discard(msg_type.strip())

            else:
                msg_types = {t.strip() for t in message_types_arg.split(",")}
        else:
            msg_types = msg_persistor.all_known_message_types()

        importer = S3MessageImporter(settings, msg_types, logger)
        logger.info(
            f"Importing the following message types from {args.start.strftime("%Y-%m-%d")} through {args.end.strftime("%Y-%m-%d")}: "
            + "".join(map(lambda t: f"\n  {t}", sorted(msg_types)))
        )
        msg_infos = importer.find_messages_in_date_range(
            start=args.start,
            end=args.end,
        )

    gb_counter = 0
    byte_counter = 0
    msg_counter = 0
    msg_text = "(not yet downloaded)"
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
            sema_obj = codec.from_dict(
                msg_dict["Payload"], auto_upgrade=False, mode="degraded"
            )
            if isinstance(sema_obj, SemaType):
                logger.debug(
                    f"Successfully parsed {sema_obj.type_name} (v{sema_obj.version}) from {msg_info.key_str} (persisted at {msg_info.persist_time.isoformat()})"
                )
                if not args.dry_run:
                    msg_persistor.persist_message(
                        msg_info.from_alias, msg_info.persist_time, sema_obj
                    )
            else:
                logger.warning(
                    f"Parsed into degraded SEMA type {sema_obj.type_name} (v{sema_obj.version}) from {msg_info.key_str}"
                )
                logger.debug(msg_text)

        except Exception as e:
            logger.error(f"Parsing failure for {msg_info.key_str}: {repr(e)}")
            logger.exception(e)
            logger.debug(msg_text)
            if args.abort_on_error:
                raise
            continue


if __name__ == "__main__":
    main()
