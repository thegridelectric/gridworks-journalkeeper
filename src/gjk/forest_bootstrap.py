"""Bootstrap/resync gw_data's registry projection from gnr's read API.

One ``g.node.forest.request`` per requested root against
``POST <api-base>/gnr/g-node-forest-request``; each response projects
through the same fan-out live broadcasts use
(``GNodeForestPersistor.project_forest``). Projection only — no
``messages`` row: message rows witness bus traffic, and an API pull is
not bus traffic. The periodic snapshot broadcast is the ongoing
anti-entropy; this is the bootstrap and the manual resync.

Run from the repo root::

    uv run python -m gjk.forest_bootstrap --api-base http://localhost:8000 d1.isone d1.time
"""

from __future__ import annotations

import argparse
import logging
import uuid

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.config import Settings
from gjk.g_node_forest_persistor import AnyForest, GNodeForestPersistor
from gjk.sema.codec import SemaCodec
from gjk.sema.types import GNodeForestRequest

LOGGER = logging.getLogger("forest_bootstrap")


def fetch_forest(api_base: str, root: str, codec: SemaCodec) -> AnyForest:
    """One forest request for one root; the decoded response."""
    req = GNodeForestRequest(roots=[root], request_id=str(uuid.uuid4()))
    resp = requests.post(
        f"{api_base}/gnr/g-node-forest-request", json=req.to_dict(), timeout=30
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("TypeName") != "g.node.forest":
        raise ValueError(
            f"expected g.node.forest for root {root}, got {payload.get('TypeName')!r}"
        )
    return codec.from_dict(payload)


def bootstrap(api_base: str, roots: list[str], settings: Settings) -> None:
    codec = SemaCodec()
    persistor = GNodeForestPersistor(
        LOGGER, registry_alias=f"{settings.service_alias.split('.')[0]}.gnr"
    )
    engine = create_engine(settings.db_url.get_secret_value())
    session_factory = sessionmaker(bind=engine)
    for root in roots:
        forest = fetch_forest(api_base, root, codec)
        with session_factory() as db, db.begin():
            persistor.project_forest(db, forest)
        LOGGER.info(
            "projected root %s: %d nodes, %d edges",
            root,
            len(forest.nodes),
            len(forest.edges),
        )
    engine.dispose()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-base",
        required=True,
        help="gnr read-API base URL (required: an assumed default could aim "
        "a projection at the wrong universe's registry)",
    )
    parser.add_argument("roots", nargs="+", help="forest-root aliases to pull")
    args = parser.parse_args()
    bootstrap(args.api_base, args.roots, Settings())


if __name__ == "__main__":
    main()
