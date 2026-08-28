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
import time
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

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

# Unknown proactor comm-infrastructure types on a separate vocabulary track,
# not part of the version reconstruction. They flood the scan's need-list on
# every window and obscure the types actually being reconstructed, so skip
# them for now. Listed explicitly (not by prefix) so an authored sibling such
# as gridworks.event.problem stays visible. Drop an entry when its word lands.
IGNORED_TYPE_NAMES = frozenset({
    "gridworks.event.comm.mqtt.connect",
    "gridworks.event.comm.mqtt.connect.failed",
    "gridworks.event.comm.mqtt.disconnect",
    "gridworks.event.comm.mqtt.fully.subscribed",
    "gridworks.event.comm.peer.active",
    "gridworks.event.comm.response.timeout",
    "gridworks.event.startup",
    "gridworks.event.shutdown",
    "gridworks.event.proactor.dbg",
    "gridworks.event.relay.report",
    "gridworks.event.relay.report.received",
    "gridworks.event.admin.command.set.relay",
    "gridworks.ping",
    "gridworks.ack",
})


def ignored_type(type_name: str) -> bool:
    """True for types deliberately excluded from the scan (see set above)."""
    return type_name in IGNORED_TYPE_NAMES


# Version sentinel for a payload with no Version field.
NO_VERSION = "<no-version>"
# Version sentinel for an object that could not be fetched/parsed into a payload.
FETCH_ERROR = "<fetch-error>"

# Specific (type_name, version) pairs deliberately REJECTED -- never authored,
# never loaded, and not surfaced as a walk-back need. Unlike IGNORED_TYPE_NAMES
# (whole types), this rejects one version of a type whose OTHER versions stay
# in scope. gridworks.event.problem carries a pre-versioning proactor shape
# (no Version field, nanosecond TimeNS) from the earliest archive; it is
# ancient and will never be used -- only the versioned gridworks.event.problem
# (reports) and the channels matter -- so its no-version pair is rejected while
# the versioned form stays visible and loadable.
# snapshot.spaceheat 000 is the pre-channel shape (a nested
# telemetry.snapshot.spaceheat keyed by node alias + telemetry name, hex enum
# symbols on some houses). It predates 2024-10-13, the start of database
# population -- the readings of that era ride gt.sh.status, which JournalKeeper
# does not accept -- so it is rejected rather than authored.
REJECTED_TYPE_VERSIONS = frozenset({
    ("gridworks.event.problem", NO_VERSION),
    ("snapshot.spaceheat", "000"),
})


def rejected_pair(type_name: str, version: str) -> bool:
    """True for a (type, version) pair deliberately rejected (see set above)."""
    return (type_name, version) in REJECTED_TYPE_VERSIONS


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
    # When loadable is False, exactly one of these explains it: the codec does
    # not know the (type, version) — a new sema word version to author — or it
    # does and the real payload still fails, a translation bug to raise.
    needs_version: bool = False
    decode_error: str | None = None


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
    """Decode one sample of each (type, version) strictly and classify.

    loadable=True: decodes cleanly. Otherwise needs_version marks a (type,
    version) the codec does not know (author it), while decode_error carries
    the failure for a version the codec DOES know — the sema definition
    mistranslating the wire.
    """
    for key, report in reports.items():
        payload = sample_payloads.get(key)
        if payload is None:
            continue
        try:
            obj = codec.from_dict(payload, auto_upgrade=False)
            report.loadable = isinstance(obj, SemaType)
        except Exception as e:  # noqa: BLE001 -- classify every decode failure
            report.loadable = False
            message = str(e)
            if "Unsupported version" in message or "Unknown type" in message:
                report.needs_version = True
            else:
                report.decode_error = message.replace("\n", " ")[:160]


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
    need_version = []
    mismatched = []
    out_of_scope = 0
    rejected = 0
    for (type_name, version), r in sorted(reports.items()):
        is_rejected = rejected_pair(type_name, version)
        if is_rejected:
            load = "rej"
        elif r.loadable:
            load = "ok"
        elif r.loadable is None:
            load = "?"
        else:
            load = "need" if r.needs_version else "MISM"
        is_accepted = type_name in accepted
        acc = "yes" if is_accepted else ("no" if accepted else "?")
        lines.append(
            f"{type_name:34} {version:>5} {r.count:>8} {load:>5} {acc:>4}  "
            f"{r.first_seen:%Y-%m-%d %H:%M}  {r.last_seen:%Y-%m-%d %H:%M}  {len(r.aliases)}"
        )
        if is_rejected:
            rejected += 1
        elif r.loadable is False:
            if not is_accepted:
                out_of_scope += 1
            elif r.needs_version:
                need_version.append((type_name, version, r.count))
            else:
                mismatched.append((type_name, version, r.count, r.decode_error))
    lines.append("=" * 100)
    if mismatched:
        lines.append(
            "TRANSLATION MISMATCH -- versions the codec knows whose real payloads "
            "fail to decode (fix the sema definition, do not add a version):"
        )
        for type_name, version, count, error in mismatched:
            lines.append(f"  - {type_name} v{version} ({count} messages): {error}")
    if need_version:
        lines.append("ACCEPTED types needing NEW sema word versions authored:")
        for type_name, version, count in need_version:
            lines.append(f"  - {type_name} v{version} ({count} messages)")
    if not mismatched and not need_version:
        lines.append("Every accepted version found decodes with the current codec.")
    if out_of_scope:
        lines.append(
            f"({out_of_scope} more non-loadable (type, version) pairs are types JK "
            f"does not accept -- out of scope.)"
        )
    if rejected:
        lines.append(
            f"({rejected} (type, version) pair(s) deliberately REJECTED -- ancient "
            f"pre-versioning shapes we will never author or load; see "
            f"REJECTED_TYPE_VERSIONS.)"
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
    parser.add_argument(
        "--save-samples",
        type=str,
        default=None,
        help="Directory to write each (type, version)'s first payload as "
        "<type.name>-<version>.json -- the wire evidence for authoring",
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
    started = time.monotonic()
    logger.info(f"listing {args.start:%Y-%m-%d}..{args.end:%Y-%m-%d}")
    infos = list_message_infos(s3, args.start, args.end, logger)
    ignored = sum(1 for i in infos if ignored_type(i.msg_type_name))
    if ignored:
        infos = [i for i in infos if not ignored_type(i.msg_type_name)]
        logger.info(
            f"ignoring {ignored} objects of {len(IGNORED_TYPE_NAMES)} deferred types"
        )
    listed = time.monotonic()
    logger.info(f"listed {len(infos)} objects; scanning versions")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        reports, sample_payloads = scan(s3, infos, args.threshold, pool)

    flag_loadable(SemaCodec(), reports, sample_payloads)
    log_report(logger, reports, accepted_types(logger))

    finished = time.monotonic()
    logger.info(
        f"elapsed {finished - started:.1f}s for {args.start:%Y-%m-%d}..{args.end:%Y-%m-%d} "
        f"(listing {listed - started:.1f}s, scanning {finished - listed:.1f}s)"
    )

    if args.save_samples is not None:
        samples_dir = Path(args.save_samples)
        samples_dir.mkdir(parents=True, exist_ok=True)
        for (type_name, version), payload in sorted(sample_payloads.items()):
            path = samples_dir / f"{type_name}-{version}.json"
            path.write_text(json.dumps(payload, indent=2) + "\n")
        logger.info(f"wrote {len(sample_payloads)} sample payloads to {samples_dir}")


if __name__ == "__main__":
    main()
