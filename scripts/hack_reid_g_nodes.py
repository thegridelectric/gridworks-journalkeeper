"""TEMPORARY (delete after it runs in prod): re-id January-seeded g_nodes.

The six hand-seeded `gridworks.g_nodes` rows carry the fleet's aliases
under GNodeIds the registry never issued. The mapping below IS the plan —
old id -> registry id, verified against the live registry read API
2026-07-30. In ONE transaction the script re-points
`installations.g_node_id`, `connectivity_edges.from/to_g_node_id`, and
the `g_nodes` primary key.

Dry-run by default; pass --execute to apply. The database comes from
GJK_DB_URL (point it at the target deliberately). Each row's alias must
match the expectation recorded here, or the script refuses.

    uv run python scripts/hack_reid_g_nodes.py
    uv run python scripts/hack_reid_g_nodes.py --execute
"""

import argparse
import os
import sys

from sqlalchemy import create_engine, text

# alias: (old January-seed id, authoritative registry GNodeId)
REID = {
    "hw1.isone.me.versant.keene.beech": (
        "8cfa8d31-aa21-46c1-879d-313fef1ba8c7",
        "4da8659f-d455-45f2-ac63-16817c1a6322",
    ),
    "hw1.isone.me.versant.keene.elm": (
        "5eb40c3f-0cad-4859-aca1-e075ea21d0a8",
        "d78d1f39-a46c-422a-9ffb-9184feda5920",
    ),
    "hw1.isone.me.versant.keene.fir": (
        "26acecc1-a67a-43e8-b89d-07575825f131",
        "db350a9b-ad7e-4da3-9365-6daa752de09e",
    ),
    "hw1.isone.me.versant.keene.maple": (
        "f3cf363c-38c2-4a20-8722-4632192b2794",
        "793ca985-8745-4d48-a7ca-850b92dacbf4",
    ),
    "hw1.isone.me.versant.keene.oak": (
        "067e8ee7-0bee-4e62-a775-956b140161ec",
        "b759f5bb-b70c-4052-8587-85e43d6a2290",
    ),
    "hw1.isone.me.versant.keene.spruce": (
        "bda8026e-28e8-4fbb-baf7-5ca38e2362a2",
        "fde9fa11-2235-4af3-8d05-ea196587d733",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true", help="apply (default: dry run)"
    )
    args = parser.parse_args()

    db_url = os.environ.get("GJK_DB_URL", "").strip().strip("'\"")
    if not db_url:
        print("GJK_DB_URL not set", file=sys.stderr)
        return 1

    eng = create_engine(db_url.replace("postgresql://", "postgresql+psycopg2://", 1))

    # Verify the database matches the plan before touching anything.
    with eng.connect() as c:
        rows = {
            str(r[0]): r[1]
            for r in c.execute(text("select id, alias from gridworks.g_nodes"))
        }
    mismatches = []
    pending = []
    for alias, (old, new) in REID.items():
        if old in rows:
            if rows[old] != alias:
                mismatches.append(
                    f"{old} holds alias {rows[old]!r}, expected {alias!r}"
                )
            else:
                pending.append((alias, old, new))
        elif new not in rows:
            mismatches.append(f"{alias}: neither old {old} nor new {new} present")
        # new already present -> this row was re-id'd earlier; idempotent skip
    if mismatches:
        print("REFUSING — database does not match the plan:", file=sys.stderr)
        for m in mismatches:
            print(f"  {m}", file=sys.stderr)
        return 1
    if not pending:
        print("nothing to do — all six rows already carry registry ids")
        return 0

    for alias, old, new in pending:
        print(f"re-id {alias}: {old} -> {new}")
    if not args.execute:
        print(f"dry run — {len(pending)} re-ids planned; pass --execute to apply")
        return 0

    with eng.begin() as c:
        for _alias, old, new in pending:
            for stmt in (
                "update gridworks.installations set g_node_id = :new where g_node_id = :old",
                "update gridworks.connectivity_edges set from_g_node_id = :new where from_g_node_id = :old",
                "update gridworks.connectivity_edges set to_g_node_id = :new where to_g_node_id = :old",
                "update gridworks.g_nodes set id = :new where id = :old",
            ):
                c.execute(text(stmt), {"new": new, "old": old})
    print(f"applied {len(pending)} re-ids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
