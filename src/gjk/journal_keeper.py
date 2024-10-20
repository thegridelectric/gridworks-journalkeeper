"""JournalKeeper"""

import logging
import threading
import time
from contextlib import contextmanager

import pendulum
from gw.named_types import GwBase
from gwbase.actor_base import ActorBase
from gwbase.codec import GwCodec
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gjk.codec import pyd_to_sql, sql_to_pyd
from gjk.config import Settings
from gjk.models import (
    DataChannelSql,
    bulk_insert_datachannels,
    bulk_insert_readings,
    insert_single_message,
)
from gjk.named_types import MyChannelsEvent, ReportEvent, Report
from gjk.named_types.asl_types import TypeByName
from gjk.old_types import GridworksEventReport
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

    def local_rabbit_startup(self) -> None:
        """Overwrites base class method.
        Meant for adding addtional bindings"""
        type_names = [
            MyChannelsEvent.type_name_value(),
            ReportEvent.type_name_value(),
            Report.type_name_value(),
        ]
        routing_keys = [f"#.{tn.replace(".", "-")}" for tn in type_names]
        for rk in routing_keys:
            LOGGER.info(
                "Binding %s to %s with %s",
                self._consume_exchange,
                "ear_tx",
                rk,
            )
            self._single_channel.queue_bind(
                self.queue_name,
                "ear_tx",
                routing_key=rk,
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
        t = time.time()
        ft = pendulum.from_timestamp(t, tz="America/New_York").format(
            "YYYY-MM-DD HH:mm:ss.SSS"
        )
        short_alias = from_alias.split(".")[-2]
        print(f"[{ft}] {payload.type_name} from {short_alias}")
        if payload.type_name == Report.type_name_value():
            try:
                self.report
        if payload.type_name == MyChannelsEvent.type_name_value():
            try:
                self.my_channels_event_from_scada(payload)
            except Exception as e:
                raise Exception(
                    f"Trouble with my_channels_event_from_scada: {e}"
                ) from e

        elif payload.type_name == ReportEvent.type_name_value():
            try:
                self.report_event_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with report_from_scada: {e}") from e
        # old messages
        elif payload.type_name == GridworksEventReport.type_name_value():
            try:
                self.old_gridworks_event_report_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with report_from_scada: {e}") from e

    def my_channels_event_from_scada(self, t: MyChannelsEvent) -> None:
        my_channels = t.my_channels
        msg = Message(
            message_id=my_channels.message_id,
            from_alias=my_channels.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=my_channels.to_dict(),
            message_type_name=my_channels.type_name,
            message_created_ms=my_channels.message_created_ms,
        )
        print(
            f"Got channels from {my_channels.from_g_node_alias}. Look at self.channel"
        )
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(msg)):
                channels = [pyd_to_sql(ch) for ch in my_channels.channel_list]
                bulk_insert_datachannels(db, channels)

    def report_event_from_scada(self, t: ReportEvent) -> None:
        self.report_from_scada(t.report)

    def report_from_scada(self, t: Report) -> None:
        msg = Message(
            message_id=t.id,
            from_alias=t.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.message_created_ms,
        )
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(msg)):
                readings_pyd = []
                ta_alias = t.about_g_node_alias
                for ch_readings in t.channel_reading_list:
                    ch = (
                        db.query(DataChannelSql)
                        .filter_by(
                            name=ch_readings.channel_name, terminal_asset_alias=ta_alias
                        )
                        .first()
                    )
                    if ch is None:
                        raise Exception(
                            f"Did not find channel {ch_readings.channel_name} (see msg id {msg.message_id})"
                        )
                    readings_pyd.extend([
                        Reading(
                            value=ch_readings.value_list[i],
                            time_ms=ch_readings.scada_read_time_unix_ms_list[i],
                            message_id=msg.message_id,
                            data_channel=sql_to_pyd(ch),
                        )
                        for i in range(len(ch_readings.value_list))
                    ])
                # Insert the readings that go along with the message
                readings = [pyd_to_sql(r) for r in readings_pyd]
                bulk_insert_readings(db, readings)
                short_alias = t.from_g_node_alias.split(".")[-2]
                print(
                    f"Inserted {len(readings)} from {short_alias}, msg id {msg.message_id}"
                )

    def old_gridworks_event_report_from_scada(self, t: GridworksEventReport) -> None:
        msg = Message(
            message_id=t.report.id,
            from_alias=t.report.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.report.to_dict(),
            message_type_name=t.report.type_name,
            message_created_ms=t.report.message_created_ms,
        )
        self.msg = msg
        print("Set this up when loading old data")

    def main(self) -> None:
        while True:
            time.sleep(3600)
            # Once a day check S3 for missed messages?
