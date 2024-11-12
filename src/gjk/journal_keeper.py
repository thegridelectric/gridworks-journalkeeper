"""JournalKeeper"""

import logging
import threading
import time
import uuid
from contextlib import contextmanager
from typing import List

import pendulum
from gw.named_types import GwBase
from gwbase.actor_base import ActorBase
from gwbase.codec import GwCodec
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gjk.codec import pyd_to_sql, sql_to_pyd
from gjk.config import Settings
from gjk.models import (
    DataChannelSql,
    bulk_insert_datachannels,
    bulk_insert_readings,
    insert_single_message,
)
from gjk.named_types import (
    ChannelReadings,
    GridworksEventProblem,
    LayoutEvent,
    MyChannelsEvent,
    Report,
    ReportEvent,
    TicklistHallReport,
    TicklistReedReport,
)
from gjk.named_types.asl_types import TypeByName
from gjk.old_types import GridworksEventReport, ReportEvent000
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
            GridworksEventProblem.type_name_value(),
            LayoutEvent.type_name_value(),
            MyChannelsEvent.type_name_value(),
            ReportEvent.type_name_value(),
            Report.type_name_value(),
            TicklistReedReport.type_name_value(),
            TicklistHallReport.type_name_value(),
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
        self.payload = payload
        self.from_alias = from_alias
        if payload.type_name == GridworksEventProblem.type_name_value():
            try:
                self.problem_event_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with problem_event_from_scada: {e}") from e

        elif payload.type_name == LayoutEvent.type_name_value():
            try:
                self.layout_event_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with layout_event_from_scada: {e}") from e
        elif payload.type_name == MyChannelsEvent.type_name_value():
            try:
                self.my_channels_event_from_scada(payload)
            except Exception as e:
                raise Exception(
                    f"Trouble with my_channels_event_from_scada: {e}"
                ) from e
        elif (
            payload.type_name == ReportEvent.type_name_value()
            and payload.version == "020"
        ):
            try:
                self.report_event_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with report_event_from_scada: {e}") from e
        elif payload.type_name == TicklistReedReport.type_name_value():
            try:
                self.ticklist_reed_report_from_scada(from_alias, payload)
            except Exception as e:
                raise Exception(
                    f"Trouble with ticklist_reed_report_from_scada: {e}"
                ) from e
        elif payload.type_name == TicklistHallReport.type_name_value():
            try:
                self.ticklist_hall_report_from_scada(from_alias, payload)
            except Exception as e:
                raise Exception(
                    f"Trouble with ticklist_hall_report_from_scada: {e}"
                ) from e
            # todo: create table in database to store data for analysis

        # old messages
        elif payload.type_name == GridworksEventReport.type_name_value():
            try:
                self.old_gridworks_event_report_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with report_from_scada: {e}") from e
        elif (
            payload.type_name == ReportEvent.type_name_value()
            and payload.version == "000"
        ):
            try:
                self.report_event_000_from_scada(payload)
            except Exception as e:
                raise Exception(
                    f"Trouble with rreport_event_000_from_scada: {e}"
                ) from e

    def ticklist_hall_report_from_scada(
        self, from_alias: str, t: TicklistHallReport
    ) -> None:
        msg = Message(
            message_id=str(uuid.uuid4()),
            from_alias=from_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.scada_received_unix_ms,
        )
        print(
            f"Got {t.channel_name} ticklist for {t.terminal_asset_alias} with {len(t.ticklist.relative_microsecond_list)} ticks"
        )
        print(f"Inserting as {t.type_name}")
        with self.get_db() as db:
            insert_single_message(db, pyd_to_sql(msg))

    def ticklist_reed_report_from_scada(
        self, from_alias: str, t: TicklistReedReport
    ) -> None:
        msg = Message(
            message_id=str(uuid.uuid4()),
            from_alias=from_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.scada_received_unix_ms,
        )
        print(
            f"Got {t.channel_name} ticklist for {t.terminal_asset_alias} with {len(t.ticklist.relative_millisecond_list)} ticks"
        )
        print(f"Inserting as {t.type_name}")
        with self.get_db() as db:
            insert_single_message(db, pyd_to_sql(msg))

    def layout_event_from_scada(self, t: LayoutEvent) -> None:
        layout = t.layout
        msg = Message(
            message_id=layout.message_id,
            from_alias=layout.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=layout.to_dict(),
            message_type_name=layout.type_name,
            message_created_ms=layout.message_created_ms,
        )
        print("Got layout event")
        for c in layout.flow_module_components:
            print(
                f"{c.flow_node_name}: {c.flow_meter_type}, {c.hz_calc_method}, {c.constant_gallons_per_tick} ticks per gallon"
            )
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(msg)):
                channels = [pyd_to_sql(ch) for ch in layout.data_channels]
                bulk_insert_datachannels(db, channels)

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
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(msg)):
                channels = [pyd_to_sql(ch) for ch in my_channels.channel_list]
                bulk_insert_datachannels(db, channels)

    def problem_event_from_scada(self, t: GridworksEventProblem) -> None:
        msg = Message(
            message_id=t.message_id,
            from_alias=t.src,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.time_created_ms,
        )
        print(f"Got problem: {t}")
        with self.get_db() as db:
            insert_single_message(db, pyd_to_sql(msg))

    def report_event_000_from_scada(self, t: ReportEvent000) -> None:
        """
        Has unused FsmActionList, does not have StateList
        """
        report = t.report
        msg = Message(
            message_id=t.message_id,
            from_alias=t.src,
            message_persisted_ms=int(time.time() * 1000),
            payload=report.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.time_created_ms,
        )
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(msg)):
                self.insert_channel_readings(
                    report.channel_reading_list,
                    report.id,
                    report.about_g_node_alias,
                    db,
                )

    def report_event_from_scada(self, t: ReportEvent) -> None:
        report = t.report
        msg = Message(
            message_id=report.id,
            from_alias=report.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=report.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.message_created_ms,
        )
        with self.get_db() as db:
            if insert_single_message(db, pyd_to_sql(msg)):
                self.insert_channel_readings(
                    report.channel_reading_list,
                    report.id,
                    report.about_g_node_alias,
                    db,
                )

    def insert_channel_readings(
        self,
        readings: List[ChannelReadings],
        message_id: str,
        ta_alias: str,
        db: Session,
    ) -> None:
        readings_pyd = []
        for ch_readings in readings:
            ch = (
                db.query(DataChannelSql)
                .filter_by(name=ch_readings.channel_name, terminal_asset_alias=ta_alias)
                .first()
            )
            if ch is None:
                raise Exception(
                    f"Did not find channel {ch_readings.channel_name} ({ta_alias}))"
                )
            readings_pyd.extend([
                Reading(
                    value=ch_readings.value_list[i],
                    time_ms=ch_readings.scada_read_time_unix_ms_list[i],
                    message_id=message_id,
                    data_channel=sql_to_pyd(ch),
                )
                for i in range(len(ch_readings.value_list))
            ])
        # Insert the readings that go along with the message
        readings = [pyd_to_sql(r) for r in readings_pyd]
        bulk_insert_readings(db, readings)
        short_alias = ta_alias(".")[-2]
        print(f"Inserted {len(readings)} from {short_alias}, msg id {message_id}")

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
