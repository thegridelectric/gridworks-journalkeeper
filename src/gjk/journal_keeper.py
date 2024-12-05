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
from sqlalchemy.orm import sessionmaker

from gjk.codec import pyd_to_sql, sql_to_pyd
from gjk.config import Settings
from gjk.models import (
    DataChannelSql,
    bulk_insert_datachannels,
    bulk_insert_readings,
    insert_single_message,
)
from gjk.named_types import (
    GridworksEventProblem,
    LayoutLite,
    Report,
    ReportEvent,
    ScadaParams,
    SnapshotSpaceheat,
    TicklistHallReport,
    TicklistReedReport,
)
from gjk.named_types.asl_types import TypeByName
from gjk.old_types import GridworksEventReport, LayoutEvent
from gjk.type_helpers import Message, Reading
from gjk.utils import FileNameMeta, str_from_ms

LOG_FORMAT = (
    "%(levelname) -10s %(sasctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)

SCADA_NAME = "s"


class JournalKeeper(ActorBase):
    tracked_types: List[GwBase] = [
        GridworksEventProblem,
        LayoutLite,
        ReportEvent,
        TicklistHallReport,
        TicklistReedReport,
    ]

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
            LayoutLite.type_name_value(),
            LayoutEvent.type_name_value(),
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

    ########################f
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
        if payload.type_name == LayoutLite.type_name_value():
            try:
                self.layout_lite_received(payload)
            except Exception as e:
                raise Exception(f"Trouble with layout_lite_from_scada: {e}") from e
        elif payload.type_name == MyChannelsEvent.type_name_value():
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
        elif payload.type_name == SnapshotSpaceheat.type_name_value():
            try:
                self.snapshot_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with snapshot_from_scada: {e}") from e
        elif payload.type_name == ScadaParams.type_name_value():
            try:
                self.params_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with process_scada_params: {e}") from e
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
        elif payload.type_name == Report.type_name_value():
            try:
                self.report_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with report_from_scada: {e}") from e
        elif payload.type_name == LayoutEvent.type_name_value():
            try:
                self.old_layout_event_from_scada(payload)
            except Exception as e:
                raise Exception(f"Trouble with layout_event_from_scada: {e}") from e

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

    def layout_lite_received(self, layout: LayoutLite) -> None:
        msg = Message(
            message_id=layout.message_id,
            from_alias=layout.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=layout.to_dict(),
            message_type_name=layout.type_name,
            message_created_ms=layout.message_created_ms,
        )
        print("Got layout event")
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
        # print(f"Got problem: {t}")
        with self.get_db() as db:
            insert_single_message(db, pyd_to_sql(msg))

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

    def snapshot_from_scada(self, t: SnapshotSpaceheat) -> None:
        # print(f"Just got a snapshot from {t.from_g_node_alias}")
        msg = Message(
            message_id=str(uuid.uuid4()),
            from_alias=t.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.snapshot_time_unix_ms,
        )
        with self.get_db() as db:
            try:
                insert_single_message(db, pyd_to_sql(msg))
            except Exception as e:
                print(f"Trouble inserting snapshot: {e}")

    def params_from_scada(self, t: ScadaParams):
        print(f"Just got scada params: {t}")
        msg = Message(
            message_id=t.message_id,
            from_alias=t.from_g_node_alias,
            message_persisted_ms=int(time.time() * 1000),
            payload=t.to_dict(),
            message_type_name=t.type_name,
            message_created_ms=t.unix_time_ms,
        )
        # when scada params from the SCADA, record the new ones
        if t.from_name == SCADA_NAME:
            with self.get_db() as db:
                try:
                    insert_single_message(db, pyd_to_sql(msg))
                except Exception as e:
                    print(f"Trouble inserting scada params: {e}")

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

    def old_layout_event_from_scada(self, t: LayoutEvent) -> None:
        layout = t.layout
        self.layout_lite_received(layout)

    def main(self) -> None:
        while True:
            time.sleep(3600)
            # Once a day check S3 for missed messages?

    ###########################################
    # S3 related
    ###########################################

    def get_single_asset_filenames(
        self,
        start_s: int,
        duration_hrs: int,
        short_alias: str,
    ) -> List[FileNameMeta]:
        date_list = self.get_date_folder_list(start_s, duration_hrs)
        print(f"Loading filenames from folders {date_list}")
        all_fns: List[FileNameMeta] = self.get_all_filenames(date_list)
        start_ms = start_s * 1000
        end_ms = (start_s + duration_hrs * 3600) * 1000 + 400
        ta_list: List[FileNameMeta] = [
            fn
            for fn in all_fns
            if (
                ("status" in fn.type_name)
                or ("report" in fn.type_name)
                or ("snapshot" in fn.type_name)
                or ("power.watts" in fn.type_name)
                or ("keyparam.change.log" in fn.type_name)
            )
            and (short_alias in fn.from_alias)
            and (start_ms <= fn.message_persisted_ms < end_ms)
        ]

        ta_list.sort(key=lambda x: x.message_persisted_ms)
        print(f"total filenames to: {len(ta_list)}")
        print(
            f"First file persisted {str_from_ms(ta_list[0].message_persisted_ms)} America/NY"
        )
        print(
            f"Last file persisted at {str_from_ms(ta_list[-1].message_persisted_ms)} America/NY"
        )
        return ta_list

    def get_all_filenames(
        self,
        date_folder_list: List[str],
    ):
        fn_list: List[FileNameMeta] = []
        for date_folder in date_folder_list:
            prefix = f"{self.world_instance_name}/eventstore/{date_folder}/"
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.aws_bucket_name, Prefix=prefix)
            file_name_list = []
            for page in pages:
                for obj in page["Contents"]:
                    file_name_list.append(obj["Key"])

            for file_name in file_name_list:
                try:
                    from_alias = file_name.split("/")[-1].split("-")[0]
                    type_name = file_name.split("/")[-1].split("-")[1]
                    message_persisted_ms = int(file_name.split("/")[-1].split("-")[2])
                except Exception as e:
                    raise Exception(f"Failed file name parsing with {file_name}") from e
                fn_list.append(
                    FileNameMeta(
                        from_alias=from_alias,
                        type_name=type_name,
                        message_persisted_ms=message_persisted_ms,
                        file_name=file_name,
                    )
                )

        return fn_list
