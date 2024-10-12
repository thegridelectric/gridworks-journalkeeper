"""JournalKeeper"""

import functools
import logging
import threading
import time
from contextlib import contextmanager
from typing import no_type_check

from gw.named_types import GwBase
from gwbase.actor_base import ActorBase
from gwbase.codec import GwCodec
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.codec import pyd_to_sql, sql_to_pyd
from gjk.config import Settings
from gjk.models import insert_single_message, bulk_insert_readings, DataChannelSql
from gjk.named_types import GridworksEventReport
from gjk.named_types.asl_types import TypeByName
from gjk.type_helpers import Message, Reading

LOG_FORMAT = (
    "%(levelname) -10s %(sasctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class JournalKeeper(ActorBase):
    def __init__(self, settings: Settings):
        # use our knwon types
        super().__init__(settings=settings, codec=GwCodec(type_by_name=TypeByName))
        self.settings: Settings = settings
        self._consume_exchange = "ear_tx"
        engine = create_engine(settings.db_url.get_secret_value())
        self.Session = sessionmaker(bind=engine)
        self.main_thread = threading.Thread(target=self.main)

    @no_type_check
    def on_queue_declareok(self, _unused_frame) -> None:
        LOGGER.info(
            "Binding %s to %s with %s",
            self._consume_exchange,
            "ear_tx",
            "#",
        )
        cb = functools.partial(self.on_direct_message_bindok, binding="#")
        self._single_channel.queue_bind(
            self.queue_name,
            "ear_tx",
            routing_key="#",
            callback=cb,
        )

    def local_start(self) -> None:
        """This overwrites local_start in actor_base, used for additional threads.
        It cannot assume the rabbit channels are established and that
        messages can be received or sent."""
        self.main_thread.start()
        self._main_loop_running = True
        print("Just started main thread")

    def local_stop(self) -> None:
        self._main_loop_running = False
        self.main_thread.join()

    @contextmanager
    def get_db(self):
        """Context manager to provide a new session for each task."""
        session = self.Session()
        try:
            yield session
            session.commit()  # Commit if everything went well
        except Exception:
            session.rollback()  # Rollback in case of an error
            raise  # Re-raise the exception after rollback
        finally:
            session.close()  # Always close the session

    ########################
    ## Receives
    ########################

    def route_mqtt_message(self, from_alias: str, payload: GwBase) -> None:
        print(f"Got {payload.type_name}")
        if payload.type_name == GridworksEventReport.type_name_value():
            try:
                self.gridworks_event_report_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with report_from_scada: {e}") from e


    def gridworks_event_report_from_scada(self, t: GridworksEventReport) -> None:
        self.msg = Message(
            message_id=t.report.id,
            from_alias=t.report.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.report.to_dict(),
            message_type_name=t.report.type_name,
            message_created_ms=t.report.message_created_ms,
        )
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(self.msg)):
                readings = []
                for ch_readings in t.report.channel_reading_list:
                    ch = db.get(DataChannelSql, ch_readings.channel_id)
                    if ch is None:
                        raise Exception(f"Did not find channel {ch_readings.channel_id} (see msg id {msg.message_id})")
                    if ch.name != ch_readings.channel_name:
                        raise Exception(f"Expect name {ch.name} for {ch.id} .. not {ch_readings.channel_name}. (see msg id {msg.message_id})")
                    readings.append(pyd_to_sql(
                        Reading(value=ch_readings.value_list[i],
                                time_ms=ch_readings.scada_read_time_unix_ms_list[i],
                                message_id=msg.message_id,
                                data_channel=sql_to_pyd(ch)
                        ) for i in len(ch_readings.value_list)
                    ))

    def main(self) -> None:
        while True:
            time.sleep(3600)
            # Once a day check S3 for missed messages?
