import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal, NamedTuple

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
    "gw.weather.observation",
    "gw.weather.forecast",
    "gw.weather.channel.gt",
    "gw.weather.forecast.channel.gt",
    "gw.weather.forecast.bundle.gt",
    "gw.weather.location.gt",
    "gw.weather.create.cmd",
    "gw.weather.cmd.ack",
    "gw.weather.cmd.nack",
]

# Sentinel "version" for a message that raised before its version was known.
PARSE_FAIL = "<parse-fail>"


@dataclass
class VersionCounts:
    """Per-(type_name, version) tallies accumulated over one import run."""

    ok: int = 0  # decoded into a known SemaType
    degraded: int = 0  # codec returned a degraded type (version not known)
    failed: int = 0  # decode raised (keyed under version=PARSE_FAIL)


class DailyKey(NamedTuple):
    """One cell of the per-day outcome tally: the S3 key's UTC day, the
    sending alias, the decoded (or key-named) type and version, and the
    outcome (`ok` / `degraded` / `failed`)."""

    day: date
    from_alias: str
    type_name: str
    version: str
    outcome: str


class RunSummary:
    """Everything one import run counted, for the log and the JSON file.

    `versions` is the decode outcome per (type, version); `daily` the same
    split by day and sender, for reconciling against S3 listings and the
    DB after a load; the three channel tallies come from the persistors and
    are the MISM signals of a back-fill: readings that found no channel row,
    enum values outside the vendored vocabulary, and era rows the layout sync
    had to add.
    """

    def __init__(self):
        self.versions: dict[tuple[str, str], VersionCounts] = defaultdict(VersionCounts)
        self.daily: Counter[DailyKey] = Counter()
        self.dropped_readings: Counter[tuple[str, str]] = Counter()
        self.enum_fallbacks: Counter[tuple[str, str]] = Counter()
        self.era_rows: Counter[tuple[str, str]] = Counter()
        self.messages_processed = 0

    def count(
        self,
        msg_info: "S3MessageInfo",
        type_name: str,
        version: str,
        outcome: str,
    ) -> None:
        counts = self.versions[(type_name, version)]
        setattr(counts, outcome, getattr(counts, outcome) + 1)
        self.daily[
            DailyKey(
                msg_info.persist_time.date(),
                msg_info.from_alias,
                type_name,
                version,
                outcome,
            )
        ] += 1

    def take_persistor_tallies(self, msg_persistor: SemaMessagePersistor) -> None:
        for persistor in msg_persistor.custom_persistor_lookup.values():
            self.dropped_readings.update(getattr(persistor, "dropped_readings", {}))
            self.enum_fallbacks.update(getattr(persistor, "enum_fallbacks", {}))
            self.era_rows.update(getattr(persistor, "skipped_mismatches", {}))

    def to_jsonable(self) -> dict:
        return {
            "messages_processed": self.messages_processed,
            "versions": [
                {
                    "type_name": t,
                    "version": v,
                    "ok": c.ok,
                    "degraded": c.degraded,
                    "failed": c.failed,
                }
                for (t, v), c in sorted(self.versions.items())
            ],
            "daily": [
                {**k._asdict(), "day": k.day.isoformat(), "count": n}
                for k, n in sorted(self.daily.items())
            ],
            "dropped_readings": [
                {"terminal_asset_alias": ta, "channel": ch, "count": n}
                for (ta, ch), n in sorted(self.dropped_readings.items())
            ],
            "enum_fallbacks": [
                {"enum": e, "value": v, "count": n}
                for (e, v), n in sorted(self.enum_fallbacks.items())
            ],
            "era_rows": [
                {"terminal_asset_alias": ta, "channel": ch, "count": n}
                for (ta, ch), n in sorted(self.era_rows.items())
            ],
        }


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
    def __init__(
        self,
        settings: Settings,
        msg_types: set[str],
        logger,
        alias_prefix: str | None = None,
    ):
        self.settings = settings
        # Keys are <from_alias>-<type>-<ms>-<source>; the alias's first
        # segment is its universe. A prefix keeps other universes' traffic
        # (dev `d1.` houses that share the eventstore) out of the journal.
        self.alias_prefix = alias_prefix
        # An instance-role box has no default region; the bucket's is known.
        self.s3 = boto3.client("s3", region_name=settings.aws.region_name)
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
        prefix = f"{self.world_instance_name}/eventstore/{dt.strftime('%Y%m%d')}"
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.aws_bucket_name, Prefix=prefix)

        date_results: list[S3MessageInfo] = []
        for page in pages:
            for s3_object in page.get("Contents", []):
                key_str = s3_object["Key"]
                try:
                    msg_info = S3MessageInfo(key_str)
                    if self.alias_prefix and not msg_info.from_alias.startswith(
                        self.alias_prefix
                    ):
                        continue
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

    def prefetch(
        self, msg_infos: Iterable[S3MessageInfo], workers: int
    ) -> Iterator[tuple[S3MessageInfo, Future[tuple[bytes, int]]]]:
        """Yield (msg_info, download future) in listing order, keeping up to
        2*workers GETs in flight so persistence never waits on the network."""
        window: list[tuple[S3MessageInfo, Future[tuple[bytes, int]]]] = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for msg_info in msg_infos:
                window.append((msg_info, pool.submit(self.download_message, msg_info)))
                if len(window) >= 2 * workers:
                    yield window.pop(0)
            yield from window


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def log_run_summary(logger, summary: RunSummary) -> None:
    """Log the (type_name, version) tally, degraded versions, and the
    channel-level MISM signals.

    Degraded versions are the actionable output of a backfill: the codec could
    not decode them, so each needs a sema word version authored before it can
    load. Dropped readings and enum fallbacks are the next tier: the message
    decoded, but a channel or a value had no home in the vendored vocabulary.
    """
    lines = [
        "",
        "=" * 78,
        f"RUN SUMMARY (messages processed: {summary.messages_processed})",
        "-" * 78,
        f"{'type_name':40} {'version':>9} {'ok':>8} {'degraded':>9} {'failed':>7}",
        "-" * 78,
    ]
    degraded = []
    for (type_name, version), c in sorted(summary.versions.items()):
        lines.append(
            f"{type_name:40} {version:>9} {c.ok:>8} {c.degraded:>9} {c.failed:>7}"
        )
        if c.degraded:
            degraded.append((type_name, version, c.degraded))
    lines.append("=" * 78)
    if degraded:
        lines.append(
            "Degraded versions (codec cannot decode — need new sema word versions):"
        )
        for type_name, version, n in degraded:
            lines.append(f"  - {type_name} v{version} ({n} messages)")
    else:
        lines.append("No degraded versions — every accepted type decoded cleanly.")
    for title, tally in (
        (
            "Dropped readings (no channel row for the report time)",
            summary.dropped_readings,
        ),
        ("Enum fallbacks (value not in vendored enum)", summary.enum_fallbacks),
        ("Era rows added by add-only layout syncs", summary.era_rows),
    ):
        if tally:
            lines.append(f"{title}:")
            for (a, b), n in sorted(tally.items()):
                lines.append(f"  - {a} / {b} ({n})")
    lines.append("=" * 78)
    logger.info("\n".join(lines))


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
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Concurrent S3 GETs kept in flight ahead of persistence",
    )
    parser.add_argument(
        "--alias-prefix",
        type=str,
        help="Only import keys whose from-alias starts with this (e.g. 'hw1.' to keep dev-universe traffic out)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Messages per database transaction (1 = commit per message)",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        help="Write the run summary (per-version, per-day, channel tallies) to this file",
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
        # Only types whose payload carries a created time are imported: the
        # rest would get a second messages row next to the one the live
        # path wrote (SemaMessagePersistor.RECEIPT_TIME_KEYED_TYPES).
        message_types_arg = args.message_types
        if message_types_arg:
            if message_types_arg.startswith("~"):
                msg_types = msg_persistor.dedupable_message_types()
                for msg_type in message_types_arg[1:].split(","):
                    msg_types.discard(msg_type.strip())
            else:
                msg_types = {t.strip() for t in message_types_arg.split(",")}
                refused = msg_types & msg_persistor.RECEIPT_TIME_KEYED_TYPES
                if refused:
                    parser.error(
                        f"refusing to import types keyed on receipt time (no created time in the payload): {sorted(refused)}"
                    )
        else:
            msg_types = msg_persistor.dedupable_message_types()

        importer = S3MessageImporter(
            settings, msg_types, logger, alias_prefix=args.alias_prefix
        )
        logger.info(
            f"Importing the following message types from {args.start.strftime('%Y-%m-%d')} through {args.end.strftime('%Y-%m-%d')}: "
            + "".join(map(lambda t: f"\n  {t}", sorted(msg_types)))
        )
        msg_infos = importer.find_messages_in_date_range(
            start=args.start,
            end=args.end,
        )

    summary = RunSummary()
    gb_counter = 0
    byte_counter = 0
    msg_counter = 0
    msg_text = "(not yet downloaded)"
    batch: list[tuple[S3MessageInfo, SemaType]] = []

    def flush_batch() -> None:
        if not batch:
            return
        failures = msg_persistor.persist_messages([
            (i.from_alias, i.persist_time, o) for i, o in batch
        ])
        failed_ids = {id(o) for _, _, o, _ in failures}
        for info, obj in batch:
            summary.count(
                info,
                obj.type_name,
                str(obj.version),
                "failed" if id(obj) in failed_ids else "ok",
            )
        for from_alias, _, obj, e in failures:
            logger.error(
                f"Persist failure for {obj.type_name} v{obj.version} from {from_alias}: {e!r}"
            )
            if args.abort_on_error:
                raise e
        batch.clear()

    for msg_info, download in importer.prefetch(msg_infos, args.workers):
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
            (msg_bytes, msg_length) = download.result()
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
                if args.dry_run:
                    summary.count(
                        msg_info, sema_obj.type_name, str(sema_obj.version), "ok"
                    )
                else:
                    batch.append((msg_info, sema_obj))
                    if len(batch) >= args.batch_size:
                        flush_batch()
            else:
                summary.count(
                    msg_info, sema_obj.type_name, str(sema_obj.version), "degraded"
                )
                logger.warning(
                    f"Parsed into degraded SEMA type {sema_obj.type_name} (v{sema_obj.version}) from {msg_info.key_str}"
                )
                logger.debug(msg_text)

        except Exception as e:
            summary.count(msg_info, msg_info.msg_type_name, PARSE_FAIL, "failed")
            logger.error(f"Parsing failure for {msg_info.key_str}: {repr(e)}")
            logger.exception(e)
            logger.debug(msg_text)
            if args.abort_on_error:
                raise
            continue

    flush_batch()
    summary.messages_processed = msg_counter
    summary.take_persistor_tallies(msg_persistor)
    log_run_summary(logger, summary)
    if args.summary_json is not None:
        args.summary_json.write_text(json.dumps(summary.to_jsonable(), indent=1))
        logger.info(f"Wrote run summary to {args.summary_json}")


if __name__ == "__main__":
    main()
