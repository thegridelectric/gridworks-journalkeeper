"""JournalKeeper"""

import functools
import logging
import threading
import time
from contextlib import contextmanager
from typing import no_type_check
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gw.errors import GwTypeError
from gwbase.codec import GwCodec
from gjk import codec
from gw.named_types import GwBase
from gjk.named_types import GridworksEventReport
from gwbase.actor_base import ActorBase, OnReceiveMessageDiagnostic
from gjk.models import DataChannelSql, bulk_insert_messages
from gjk.config import Settings
from gjk.named_types.asl_types import TypeByName
from gjk.utils import tuple_to_msg

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
        report = t.report
        print(f"Got Report from {report.from_g_node_alias}")
        readings = report.channel_reading_list
        # TODO - turn this into a bunch of ReadingSqls to be bulk insreted
        with self.get_db() as db:
            try:
                db.add(tuple_to_msg(report))
                db.commit()
                # TODO: also add the various readings
            except Exception:
                pass # probably a repeat report

    def main(self)-> None:
        while True:
            time.sleep(3600)
            # Once a day check S3 for missed messages?