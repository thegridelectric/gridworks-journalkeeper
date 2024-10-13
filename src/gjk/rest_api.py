from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from gjk.api.csv_maker import csv_maker_router
from gjk.api_db import get_db
from gjk.codec import sql_to_pyd
from gjk.models import DataChannelSql
from gjk.named_types import DataChannelGt

# Initialize
app = FastAPI()
app.include_router(csv_maker_router)


@app.get("/hello")
def get_hello():
    return {"hi": "there"}


@app.get("/data-channels/{short_alias}", response_model=List[DataChannelGt])
def get_data_channels(
    short_alias: str, db: Session = Depends(get_db)
) -> List[DataChannelGt]:
    sql_channels = (
        db.query(DataChannelSql)
        .filter(DataChannelSql.terminal_asset_alias.like(f"%{short_alias}%"))
        .all()
    )
    channels = sorted([sql_to_pyd(ch) for ch in sql_channels], key=lambda ch: ch.name)
    return channels
