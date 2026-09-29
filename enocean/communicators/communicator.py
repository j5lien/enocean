"""The Communicator base class: packet parsing, queues, base ID, teach-in, statistics and health."""

import logging
import queue
import threading
import time
from collections.abc import Callable
from typing import TypeGuard

from enocean.devices import Device, DeviceRegistry
from enocean.protocol.constants import PACKET, PARSE_RESULT, RETURN_CODE, RORG
from enocean.protocol.packet import Packet, RadioPacket, ResponsePacket, UTETeachInPacket, enum_name
from enocean.stats import CommunicatorStats, Health
from enocean.utils import to_hex_string


def packet_log_fields(packet: Packet, event: str | None = None) -> dict[str, object]:
    """Fields attached to log records about a packet, for structured log handlers.

    The same names and formats as Packet.to_dict(): enum names, hex IDs.

    Args:
        packet: The packet the record is about.
        event: The record's `event` field (e.g. 'packet_received'), to filter records by kind.
    """
    fields: dict[str, object] = {'packet_type': enum_name(PACKET, packet.packet_type)}
    if event is not None:
        fields['event'] = event
    if isinstance(packet, RadioPacket):
        eep_id = packet.eep_id
        fields.update(
            rorg=enum_name(RORG, packet.rorg),
            sender=packet.sender_hex,
            destination=packet.destination_hex,
            dbm=packet.dbm,
            status=packet.status,
            repeater_count=packet.repeater_count,
            eep=str(eep_id) if eep_id else None,
        )
    return fields


class Communicator(threading.Thread):
    """Base class of the transports: a thread parsing ESP3 bytes into packets and sending packets.

    Use SerialCommunicator or TCPCommunicator. Received packets are put in the `receive` queue, or passed to
    `callback`; `send()` queues packets for the transport to write. Every communicator keeps `stats` and reports its
    `health()`.

    Args:
        callback: Called with each received packet (from the communicator thread) instead of queueing it in `receive`.
        teach_in: Answer UTE teach-in requests at any time. With False, only during learn().
        devices: Decode received telegrams with the profile of their device, and drop those of ignored devices.
    """

    logger = logging.getLogger('enocean.communicators.Communicator')

    def __init__(
        self,
        callback: Callable[[Packet], None] | None = None,
        teach_in: bool = True,
        devices: DeviceRegistry | None = None,
    ) -> None:
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
        self._base_id_requested_at = 0.0
        self._base_id_received = threading.Event()
        # UTE teach-in requests waiting for the Base ID before they can be answered
        self._pending_teach_ins: list[UTETeachInPacket] = []
        # Teach-in window opened by learn(): answer teach-ins until then (time.monotonic()), collecting the devices
        self._learning_until = 0.0
        self._learned: list[Device] = []
        # Known devices: received telegrams are decoded with their profile, ignored devices dropped
        self.devices = devices
        # Runtime statistics, see enocean.stats
        self.stats = CommunicatorStats()
        # Set by transports while their port/socket is usable
        self._transport_ready = False
        # Should new messages be learned automatically? Defaults to True.
        # TODO: Not sure if we should use CO_WR_LEARNMODE??
        self.teach_in = teach_in

    def _get_from_send_queue(self) -> Packet | None:
        """Get message from send queue, if one exists."""
        try:
            packet = self.transmit.get(block=False)
            self.logger.debug('Sending %s', packet, extra=packet_log_fields(packet, 'packet_sent'))
            return packet
        except queue.Empty:
            pass
        return None

    def send(self, packet: Packet) -> bool:
        """Queue a packet for the transport to write.

        Returns:
            False if packet isn't a Packet.
        """
        if not isinstance(packet, Packet):
            self.logger.error('Object to send must be an instance of Packet', extra={'event': 'invalid_packet'})
            return False
        self.transmit.put(packet)
        return True

    def _feed(self, data: bytes | bytearray) -> None:
        """Appends bytes read from the transport to the parse buffer."""
        self._buffer.extend(bytearray(data))
        self.stats.record_bytes_received(len(data))

    def stop(self) -> None:
        """Ask the communicator thread to stop; join() it to wait until it has."""
        self._stop_flag.set()

    def parse(self) -> PARSE_RESULT:
        """Parses messages and puts them to receive queue."""
        # Loop while we get new messages
        while True:
            status, self._buffer, packet = Packet.parse_msg(self._buffer, on_error=self.stats.record_parse_error)
            # If message is incomplete -> break the loop
            if status == PARSE_RESULT.INCOMPLETE:
                return status

            # If message is OK, add it to receive queue or send to the callback method
            if status == PARSE_RESULT.OK and packet:
                self.stats.record_received(packet)

                if self.devices is not None and isinstance(packet, RadioPacket):
                    if self.devices.is_ignored(packet.sender):
                        self.stats.record_ignored()
                        continue
                    self.devices.decode(packet)

                if self._base_id_requested and self._is_base_id_response(packet):
                    self._base_id = packet.response_data
                    base_id = to_hex_string(self._base_id)
                    self.logger.info(
                        'Base ID of the module: %s', base_id, extra={'event': 'base_id_received', 'base_id': base_id}
                    )
                    self._base_id_requested = False
                    self.stats.record_base_id_received(time.monotonic() - self._base_id_requested_at)
                    self._base_id_received.set()
                    self._answer_pending_teach_ins()

                if isinstance(packet, UTETeachInPacket) and (self.teach_in or self.learning):
                    self._pending_teach_ins.append(packet)
                    if self.base_id is not None:
                        self._answer_pending_teach_ins()

                self.logger.debug('Received %s', packet, extra=packet_log_fields(packet, 'packet_received'))
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
            response, outcome = self._teach_in_outcome(packet)
            self.logger.info(
                'UTE teach-in request from %s (EEP %s): %s.',
                packet.sender_hex,
                packet.eep_id,
                outcome,
                extra={**packet_log_fields(packet, 'teach_in'), 'outcome': outcome},
            )
            self.send(packet.create_response_packet(self._base_id, response))
            self.stats.record_teach_in_response()

    def _teach_in_outcome(self, packet: UTETeachInPacket) -> tuple[list[bool], str]:
        """The response to a UTE teach-in request, updating the device registry.

        Deletion for deletion requests (and for non-specific ones from devices already known), refusal for unknown
        profiles, acceptance otherwise.
        """
        known = self.devices is not None and packet.sender_hex in self.devices
        if packet.request_type == UTETeachInPacket.DELETE or (
            packet.request_type == UTETeachInPacket.NOT_SPECIFIC and known
        ):
            if self.devices is not None:
                self.devices.remove(packet.sender)
            return UTETeachInPacket.DELETE_ACCEPTED, 'deleted'
        eep_id = packet.eep_id
        known_profiles = packet.eep.telegrams
        if eep_id is None or eep_id.type not in known_profiles.get(eep_id.rorg, {}).get(eep_id.func, {}):
            return UTETeachInPacket.EEP_NOT_SUPPORTED, 'profile not supported'
        device = Device(packet.sender_hex, eep_id)
        if self.devices is not None and not known:
            self.devices.add(device)
        if self.learning:
            self._learned.append(device)
        return UTETeachInPacket.TEACHIN_ACCEPTED, 'accepted'

    @property
    def learning(self) -> bool:
        """Whether a teach-in window opened by learn() is ongoing."""
        return time.monotonic() < self._learning_until

    def learn(self, timeout: float = 30, max_devices: int | None = None) -> list[Device]:
        """Open a teach-in window: answer UTE teach-in requests, even with teach_in=False.

        Put the devices in learn mode meanwhile (e.g. press their learn button). Taught-in devices are added to
        `devices` (a DeviceRegistry is created if there is none). Blocks: call it from another thread than the
        communicator's.

        Args:
            timeout: How long the window stays open, in seconds.
            max_devices: Close the window once this many devices are taught in.

        Returns:
            The devices taught in.
        """
        if self.devices is None:
            self.devices = DeviceRegistry()
        self._learned = []
        self._learning_until = time.monotonic() + timeout
        try:
            while self.learning and (max_devices is None or len(self._learned) < max_devices):
                time.sleep(0.05)
        finally:
            self._learning_until = 0.0
        return list(self._learned)

    def _request_base_id(self) -> None:
        if not self._base_id_requested:
            self._base_id_requested = True
            self._base_id_requested_at = time.monotonic()
            self._base_id_received.clear()
            self.stats.record_base_id_request()
            # Send COMMON_COMMAND 0x08, CO_RD_IDBASE request to the module
            self.send(Packet(PACKET.COMMON_COMMAND, data=[0x08]))

    def health(self, max_silence: float | None = None) -> Health:
        """Current state, e.g. for a liveness/readiness probe.

        Args:
            max_silence: Seconds without receiving any packet that count as a problem (after startup, the delay counts
                from the communicator's creation). None to ignore silence.

        Returns:
            The state; `healthy` is False and `problems` says why when something is wrong.
        """
        snapshot = self.stats.snapshot()
        silence = time.time() - (snapshot.last_packet_received_at or snapshot.started_at)
        running = self.is_alive() and not self._stop_flag.is_set()
        problems = []
        if not running:
            problems.append('communicator thread is not running')
        if not self._transport_ready:
            problems.append('transport is not ready')
        if max_silence is not None and silence > max_silence:
            problems.append('no packet received for %.0f s' % silence)
        return Health(
            running=running,
            transport_ready=self._transport_ready,
            base_id_known=self._base_id is not None,
            receive_queue_size=self.receive.qsize(),
            transmit_queue_size=self.transmit.qsize(),
            seconds_since_last_packet=silence,
            problems=tuple(problems),
        )

    @property
    def base_id(self) -> list[int] | None:
        """The module's base ID, the first of the 128 IDs it can send from; asked to the module when unknown.

        Waits up to a second for the module's response, except from the communicator thread itself, which can't wait
        for a response only it can read: there the request is sent and None returned until it arrives.
        """
        if self._base_id is not None:
            return self._base_id

        self._request_base_id()
        if threading.current_thread() is not self and not self._base_id_received.wait(1):
            self.logger.warning(
                'No response from the module to the Base ID request.', extra={'event': 'base_id_timeout'}
            )
            self.stats.record_base_id_timeout()
            self._base_id_requested = False
        # Return the current Base ID (might be None).
        return self._base_id

    @base_id.setter
    def base_id(self, base_id: list[int] | None) -> None:
        """Sets the Base ID without asking the module, e.g. when it is already known."""
        self._base_id = base_id
