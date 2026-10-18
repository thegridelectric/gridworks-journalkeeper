"""Word versions the journal refuses: a message at one of these is
retired before decode, on the live path and on an S3 replay alike,
so a re-run of the archive never brings them back.

The vendored snapshot holds none of these versions, so the codec
would refuse them anyway; naming them here makes the refusal a
counted outcome instead of a decode error. The `gw.weather.*` words
below are the versions the weather service emitted before its
station words; their rows left the journal on 2026-10-18 and remain
in the persistent store.
"""

from typing import Any

RETIRED_VERSIONS: dict[str, frozenset[str]] = {
    "gw.weather.channel.gt": frozenset({"000", "001"}),
    "gw.weather.create.cmd": frozenset({"000", "001"}),
    "gw.weather.forecast": frozenset({"000"}),
    "gw.weather.forecast.bundle.gt": frozenset({"000", "001"}),
    "gw.weather.location.gt": frozenset({"000"}),
    "gw.weather.observation": frozenset({"000"}),
}


def is_retired(payload: dict[str, Any]) -> bool:
    """True when the bare sema dict names a retired (TypeName, Version)."""
    versions = RETIRED_VERSIONS.get(payload.get("TypeName", ""))
    return versions is not None and payload.get("Version") in versions
