"""JournalKeeper"""

import functools
import logging
import time
import threading
from typing import no_type_check

from gw.named_types import GwBase
from gw.enums import MessageCategorySymbol
from gwbase.actor_base import ActorBase
from gwbase.actor_base import OnReceiveMessageDiagnostic
from gwbase.enums import GNodeRole, UniverseType
from gw.errors import GwTypeError
from gjk.config import Settings
from gjk.types import GridworksEventReport, PowerWatts, KeyparamChangeLog, MyDataChannels
from gjk.

LOG_FORMAT = (
    "%(levelname) -10s %(sasctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class JournalKeeper(ActorBase):
    def __init__(self, settings: Settings):
        super().__init__(settings=settings)
        self.settings: Settings = settings
        self._consume_exchange = "ear_tx"
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

    ########################
    ## Receives
    ########################

    def route_mqtt_message(self, from_alias: str, payload: GwBase) -> None:
        if payload.type_name == HeartbeatA.type_name:
            if from_role != GNodeRole.Supervisor:
                LOGGER.info(
                    f"Ignoring HeartbeatA from GNode {from_alias} with GNodeRole {from_role}; expects"
                    f"Supervisor as the GNodeRole",
                )
                return
            elif from_alias != self.settings.my_super_alias:
                LOGGER.info(
                    f"Ignoring HeartbeatA from supervisor {from_alias}; "
                    f"my supervisor is {self.settings.my_super_alias}",
                )
                return

            try:
                self.heartbeat_from_super(from_alias, payload)


    @no_type_check
    def on_message(self, _unused_channel, basic_deliver, properties, body) -> None:
        """
        Overriding actor_base on_message
        """
        routing_key = basic_deliver.routing_key
        LOGGER.debug(
            f"{self.alias}: Got {basic_deliver.routing_key} with delivery tag {basic_deliver.delivery_tag}"
        )
        self.acknowledge_message(basic_deliver.delivery_tag)

        try:
            type_name = self.get_payload_type_name(basic_deliver)
        except GwTypeError:
            return
        try:
            from_alias = self.from_alias_from_routing_key(routing_key)
        except GwTypeError as e:
            self._latest_on_message_diagnostic = (
                OnReceiveMessageDiagnostic.FROM_GNODE_DECODING_PROBLEM
            )
            LOGGER.warning(
                f"IGNORING MESSAGE. {self._latest_on_message_diagnostic}: {e}"
            )
            return


        try:
            msg_category = self.message_category_from_routing_key(routing_key)
        except GwTypeError:
            return

        if self.settings.logging_on or self.settings.log_message_summary:
            print(f"{pendulum.now('UTC')} MSG :  {from_alias} sent {type_name}")
        kafka_topic = f"{from_alias}-{type_name}"
        if msg_category == MessageCategory.RabbitGwSerial:
            file_name = (
                f"{kafka_topic}-{int(time.time() * 1000)}-{self.settings.my_fqdn}.txt"
            )
        else:
            file_name = (
                f"{kafka_topic}-{int(time.time() * 1000)}-{self.settings.my_fqdn}.json"
            )

        if self.use_s3 and self.s3_put_works:
            success_putting_this_one = self.put_in_s3(file_name, body)
        else:
            success_putting_this_one = False
        self.last_file_name = file_name
        self.last_body = body
        if not success_putting_this_one:
            self.store_locally(file_name, body)