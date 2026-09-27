import datetime
import logging
import queue
import threading
from collections.abc import Callable
from typing import TypeGuard

from enocean.protocol.constants import PACKET, PARSE_RESULT, RETURN_CODE
from enocean.protocol.packet import Packet, RadioPacket, ResponsePacket, UTETeachInPacket
from enocean.utils import to_hex_string


def packet_log_fields(packet: Packet) -> dict[str, object]:
    """Fields attached to log records about a packet, for structured log handlers."""
    fields: dict[str, object] = {'packet_type': int(packet.packet_type)}
    if isinstance(packet, RadioPacket):
        fields['rorg'] = int(packet.rorg)
        fields['sender'] = packet.sender_hex
        fields['dbm'] = packet.dBm
    return fields


class Communicator(threading.Thread):
    """
    Communicator base-class for EnOcean.
    Not to be used directly, only serves as base class for SerialCommunicator etc.
    """

    logger = logging.getLogger('enocean.communicators.Communicator')

    def __init__(self, callback: Callable[[Packet], None] | None = None, teach_in: bool = True) -> None:
        super().__init__()
        # Create an event to stop the thread
        self._stop_flag = threading.Event()
        # Input buffer
        self._buffer: list[int] = []
        # Setup packet queues
        self.transmit: queue.Queue[Packet] = queue.Queue()
        self.receive: queue.Queue[Packet] = queue.Queue()
        # Set the callback method
        self.__callback = callback
        # Internal variable for the Base ID of the module.
        self._base_id: list[int] | None = None
        # Set while a CO_RD_IDBASE request is waiting for its response
        self._base_id_requested = False
        self._base_id_received = threading.Event()
        # UTE teach-in requests waiting for the Base ID before they can be answered
        self._pending_teach_ins: list[UTETeachInPacket] = []
        # Should new messages be learned automatically? Defaults to True.
        # TODO: Not sure if we should use CO_WR_LEARNMODE??
        self.teach_in = teach_in

    def _get_from_send_queue(self) -> Packet | None:
        """Get message from send queue, if one exists"""
        try:
            packet = self.transmit.get(block=False)
            self.logger.debug('Sending %s', packet, extra=packet_log_fields(packet))
            return packet
        except queue.Empty:
            pass
        return None

    def send(self, packet: Packet) -> bool:
        if not isinstance(packet, Packet):
            self.logger.error('Object to send must be an instance of Packet')
            return False
        self.transmit.put(packet)
        return True

    def stop(self) -> None:
        self._stop_flag.set()

    def parse(self) -> PARSE_RESULT:
        """Parses messages and puts them to receive queue"""
        # Loop while we get new messages
        while True:
            status, self._buffer, packet = Packet.parse_msg(self._buffer)
            # If message is incomplete -> break the loop
            if status == PARSE_RESULT.INCOMPLETE:
                return status

            # If message is OK, add it to receive queue or send to the callback method
            if status == PARSE_RESULT.OK and packet:
                packet.received = datetime.datetime.now()

                if self._base_id_requested and self._is_base_id_response(packet):
                    self._base_id = packet.response_data
                    self.logger.info('Base ID of the module: %s', to_hex_string(self._base_id))
                    self._base_id_requested = False
                    self._base_id_received.set()
                    self._answer_pending_teach_ins()

                if isinstance(packet, UTETeachInPacket) and self.teach_in:
                    self._pending_teach_ins.append(packet)
                    if self.base_id is not None:
                        self._answer_pending_teach_ins()

                self.logger.debug('Received %s', packet, extra=packet_log_fields(packet))
                if self.__callback is None:
                    self.receive.put(packet)
                else:
                    self.__callback(packet)

    @staticmethod
    def _is_base_id_response(packet: Packet) -> TypeGuard[ResponsePacket]:
        return (
            isinstance(packet, ResponsePacket)
            and packet.packet_type == PACKET.RESPONSE
            and packet.response == RETURN_CODE.OK
            and len(packet.response_data) == 4
        )

    def _answer_pending_teach_ins(self) -> None:
        if self._base_id is None:
            return
        while self._pending_teach_ins:
            packet = self._pending_teach_ins.pop(0)
            if packet.sender == self._base_id:
                continue
            self.logger.info(
                'Answering UTE teach-in from %s (EEP %02X-%02X-%02X).',
                packet.sender_hex,
                packet.rorg_of_eep,
                packet.rorg_func,
                packet.rorg_type,
                extra=packet_log_fields(packet),
            )
            self.send(packet.create_response_packet(self._base_id))

    def _request_base_id(self) -> None:
        if not self._base_id_requested:
            self._base_id_requested = True
            self._base_id_received.clear()
            # Send COMMON_COMMAND 0x08, CO_RD_IDBASE request to the module
            self.send(Packet(PACKET.COMMON_COMMAND, data=[0x08]))

    @property
    def base_id(self) -> list[int] | None:
        """
        Fetches Base ID from the transmitter, if required. Otherwise returns the currently set Base ID.
        Waits up to a second for the module's response, except from the communicator thread itself, which can't
        wait for a response only it can read: there the request is sent and None returned until it arrives.
        """
        if self._base_id is not None:
            return self._base_id

        self._request_base_id()
        if threading.current_thread() is not self and not self._base_id_received.wait(1):
            self.logger.warning('No response from the module to the Base ID request.')
            self._base_id_requested = False
        # Return the current Base ID (might be None).
        return self._base_id

    @base_id.setter
    def base_id(self, base_id: list[int] | None) -> None:
        """Sets the Base ID manually, only for testing purposes."""
        self._base_id = base_id
