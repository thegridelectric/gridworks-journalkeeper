"""Discover which sema (type_name, version) pairs appear in the S3 event store.

The backfill (loading the event store into gw_data back to Sept 2024) has to
know *which message versions appear when* before it loads anything: a version
outside the current sema registry decodes degraded and cannot be stored, so it
must be authored as a new sema word version first. Finding that out by
downloading every object is untenable -- the loader's GETs are sequential and
(from a dev box) cross-region, on the order of hours per day.

This scan answers the question cheaply, for two reasons:

1. The version is a plain field in the JSON envelope (``Payload.Version``), so
   reading it needs only ``json.loads`` -- no codec, no decode, no degraded
   handling.
2. A type's version is piecewise-constant in time (it flips only at a deploy).
   So per ``(type_name, from_alias)`` the scan **downloads all** objects only
   when the bucket is small (< ``DOWNLOAD_ALL_THRESHOLD`` over the span), and
   otherwise **bisects** the time-sorted keys to pin every version-change
   boundary in O(log n) GETs. A stable high-volume type costs two GETs.

Keying by ``from_alias`` as well as ``type_name`` matters: different houses can
run different versions at the same time, which would break the piecewise-
constant assumption if their objects were pooled.

Output is a ``(type_name, version)`` timeline -- count, first/last seen, and
the houses that emitted it -- and one sample of each pair is run through the
codec to flag the versions that still need a sema word version authored.

Run it per week to match the backwards week-by-week backfill workflow::

    python -m gjk.version_scan --start 2025-12-26 --end 2026-01-01

Caveat: bisection can miss a version whose entire run sits strictly inside an
interval whose endpoints share a version. That needs a version to appear,
vanish, and be replaced between two probes -- not a real deploy shape for the
churny config types, which are low-volume and taken by the download-all path
anyway.
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import boto3

from gjk.config import Settings
from gjk.s3_message_importer import S3MessageInfo
from gjk.sema import SemaCodec, SemaType
from gjk.sema_message_persistor import SemaMessagePersistor

# Mirror the constants baked into s3_message_importer.S3MessageImporter.
AWS_BUCKET_NAME = "gwdev"
WORLD_INSTANCE_NAME = "hw1__1"

# Per (type_name, from_alias) over the scanned span: fewer than this many
# objects -> read every version directly; at or above -> bisect for boundaries.
DOWNLOAD_ALL_THRESHOLD = 100

# Version sentinel for a payload with no Version field.
NO_VERSION = "<no-version>"
# Version sentinel for an object that could not be fetched/parsed into a payload.
FETCH_ERROR = "<fetch-error>"


@dataclass
class Segment:
    """A maximal run of one version within a time-sorted (type, alias) bucket.

    start and end are inclusive indices into that sorted bucket.
    """

    version: str
    start: int
    end: int


@dataclass
class TypeVersionReport:
    """One (type_name, version) pair observed across the scanned span.

    type_name and version are the raw dotted TypeName and version string read
    from the JSON envelope (Payload.TypeName / Payload.Version), not codec
    output -- a version the registry never had still shows up here. loadable is
    None until a sample payload is run through the codec.
    """

    type_name: str
    version: str
    count: int
    first_seen: datetime
    last_seen: datetime
    aliases: set[str] = field(default_factory=set)
    loadable: bool | None = None


def dates_in_range(start: datetime, end: datetime):
    dt = start
    while dt <= end:
        yield dt
        dt += timedelta(days=1)


def list_message_infos(
    s3, start: datetime, end: datetime, logger
) -> list[S3MessageInfo]:
    """List (do not download) every event-store object in the inclusive range."""
    infos: list[S3MessageInfo] = []
    unparseable = 0
    paginator = s3.get_paginator("list_objects_v2")
    for dt in dates_in_range(start, end):
        prefix = f"{WORLD_INSTANCE_NAME}/eventstore/{dt:%Y%m%d}"
        for page in paginator.paginate(Bucket=AWS_BUCKET_NAME, Prefix=prefix):
            for obj in page.get("Contents", []):
                try:
                    infos.append(S3MessageInfo(obj["Key"]))
                except Exception:  # noqa: BLE001 -- malformed key, count and skip
                    unparseable += 1
    if unparseable:
        logger.warning(f"skipped {unparseable} objects with unparseable keys")
    return infos


def fetch_payload(s3, key_str: str) -> dict:
    """Return an object's sema payload dict.

    Most event-store objects wrap it as ``{"Header", "Payload", "TypeName"}``;
    a few store the payload at top level. Fall back to the whole document so
    both shapes yield a dict carrying TypeName/Version.
    """
    obj = s3.get_object(Bucket=AWS_BUCKET_NAME, Key=key_str)
    document = json.loads(obj["Body"].read())
    payload = document.get("Payload", document)
    if not isinstance(payload, dict):
        raise ValueError(f"payload is not a JSON object for {key_str}")
    return payload


def find_boundaries(
    lo: int, hi: int, load_version: Callable[[int], str], boundaries: set[int]
) -> None:
    """Record every index b in [lo, hi) where version[b] != version[b + 1]."""
    if load_version(lo) == load_version(hi):
        return
    if hi - lo == 1:
        boundaries.add(lo)
        return
    mid = (lo + hi) // 2
    find_boundaries(lo, mid, load_version, boundaries)
    find_boundaries(mid, hi, load_version, boundaries)


def scan_bucket(
    s3,
    bucket: list[S3MessageInfo],
    threshold: int,
    pool: ThreadPoolExecutor,
    sample_payloads: dict[tuple[str, str], dict],
) -> list[Segment]:
    """Return the version segments for one time-sorted (type, alias) bucket."""
    n = len(bucket)
    version_at: dict[int, str] = {}

    def load_version(i: int) -> str:
        if i not in version_at:
            try:
                payload = fetch_payload(s3, bucket[i].key_str)
                version = str(payload.get("Version", NO_VERSION))
                sample_payloads.setdefault((bucket[i].msg_type_name, version), payload)
            except Exception:  # noqa: BLE001 -- unfetchable object, match importer's skip
                version = FETCH_ERROR
            version_at[i] = version
        return version_at[i]

    if n < threshold:
        list(pool.map(load_version, range(n)))
        boundaries = {i for i in range(n - 1) if version_at[i] != version_at[i + 1]}
    else:
        boundaries = set()
        find_boundaries(0, n - 1, load_version, boundaries)

    starts = [0] + [b + 1 for b in sorted(boundaries)]
    ends = sorted(boundaries) + [n - 1]
    return [Segment(version_at[s], s, e) for s, e in zip(starts, ends)]


def scan(
    s3,
    infos: list[S3MessageInfo],
    threshold: int,
    pool: ThreadPoolExecutor,
) -> tuple[dict[tuple[str, str], TypeVersionReport], dict[tuple[str, str], dict]]:
    """Bucket by (type, alias), scan each, aggregate into per-(type, version) reports."""
    buckets: dict[tuple[str, str], list[S3MessageInfo]] = defaultdict(list)
    for info in infos:
        buckets[(info.msg_type_name, info.from_alias)].append(info)

    reports: dict[tuple[str, str], TypeVersionReport] = {}
    sample_payloads: dict[tuple[str, str], dict] = {}
    for (type_name, alias), bucket in buckets.items():
        bucket.sort(key=lambda x: x.persist_time)
        for seg in scan_bucket(s3, bucket, threshold, pool, sample_payloads):
            key = (type_name, seg.version)
            count = seg.end - seg.start + 1
            first = bucket[seg.start].persist_time
            last = bucket[seg.end].persist_time
            report = reports.get(key)
            if report is None:
                reports[key] = TypeVersionReport(
                    type_name=type_name,
                    version=seg.version,
                    count=count,
                    first_seen=first,
                    last_seen=last,
                    aliases={alias},
                )
            else:
                report.count += count
                report.first_seen = min(report.first_seen, first)
                report.last_seen = max(report.last_seen, last)
                report.aliases.add(alias)
    return reports, sample_payloads


def flag_loadable(
    codec: SemaCodec,
    reports: dict[tuple[str, str], TypeVersionReport],
    sample_payloads: dict[tuple[str, str], dict],
) -> None:
    """Decode one sample of each (type, version); set loadable = decodes cleanly."""
    for key, report in reports.items():
        payload = sample_payloads.get(key)
        if payload is None:
            continue
        try:
            obj = codec.from_dict(payload, auto_upgrade=False, mode="degraded")
            report.loadable = isinstance(obj, SemaType)
        except Exception:  # noqa: BLE001 -- a decode failure is "not loadable"
            report.loadable = False


def accepted_types(logger) -> set[str]:
    """The message types JournalKeeper accepts -- the backfill's real scope.

    Built from the persistor's own registry. Returns an empty set (annotate as
    unknown) if settings cannot be constructed, so the scan still runs.
    """
    try:
        persistor = SemaMessagePersistor(Settings(), SemaCodec(), logger)
        return persistor.all_known_message_types()
    except Exception as e:  # noqa: BLE001 -- annotation is best-effort
        logger.warning(f"could not load accepted types ({e!r}); annotating all as '?'")
        return set()


def log_report(
    logger, reports: dict[tuple[str, str], TypeVersionReport], accepted: set[str]
) -> None:
    lines = [
        "",
        "=" * 100,
        "S3 VERSION SCAN",
        "-" * 100,
        f"{'type_name':34} {'ver':>5} {'count':>8} {'load':>5} {'acc':>4}  "
        f"{'first_seen':16}  {'last_seen':16}  houses",
        "-" * 100,
    ]
    need_authoring = []
    out_of_scope = 0
    for (type_name, version), r in sorted(reports.items()):
        load = "ok" if r.loadable else ("NO" if r.loadable is False else "?")
        is_accepted = type_name in accepted
        acc = "yes" if is_accepted else ("no" if accepted else "?")
        lines.append(
            f"{type_name:34} {version:>5} {r.count:>8} {load:>5} {acc:>4}  "
            f"{r.first_seen:%Y-%m-%d %H:%M}  {r.last_seen:%Y-%m-%d %H:%M}  {len(r.aliases)}"
        )
        if r.loadable is False:
            if is_accepted:
                need_authoring.append((type_name, version, r.count))
            else:
                out_of_scope += 1
    lines.append("=" * 100)
    if need_authoring:
        lines.append(
            "ACCEPTED versions the codec cannot decode -- need new sema word versions:"
        )
        for type_name, version, count in need_authoring:
            lines.append(f"  - {type_name} v{version} ({count} messages)")
    else:
        lines.append("Every accepted version found decodes with the current codec.")
    if out_of_scope:
        lines.append(
            f"({out_of_scope} more non-loadable (type, version) pairs are types JK "
            f"does not accept -- out of scope.)"
        )
    lines.append("=" * 100)
    logger.info("\n".join(lines))


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scan the S3 event store for the (type_name, version) inventory of a date range"
    )
    parser.add_argument(
        "--start", type=_parse_date, required=True, help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", type=_parse_date, required=True, help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DOWNLOAD_ALL_THRESHOLD,
        help="Per (type, alias): download all below this count, else bisect",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=32,
        help="Concurrent S3 GETs for the download-all path",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel("DEBUG" if args.verbose else "INFO")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

    s3 = boto3.client("s3")
    logger.info(f"listing {args.start:%Y-%m-%d}..{args.end:%Y-%m-%d}")
    infos = list_message_infos(s3, args.start, args.end, logger)
    logger.info(f"listed {len(infos)} objects; scanning versions")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        reports, sample_payloads = scan(s3, infos, args.threshold, pool)

    flag_loadable(SemaCodec(), reports, sample_payloads)
    log_report(logger, reports, accepted_types(logger))


if __name__ == "__main__":
    main()
