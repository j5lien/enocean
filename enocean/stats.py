"""
Runtime statistics and health of a communicator, always collected (no dependency, negligible cost).

Read them with `communicator.stats.snapshot()` and `communicator.health()`, or expose them to Prometheus with
`enocean.prometheus`.
"""

import threading
import time
from collections import Counter, OrderedDict
from dataclasses import dataclass, field

from enocean.protocol.packet import DATA_CRC_ERROR, HEADER_CRC_ERROR, MALFORMED_PACKET, Packet, RadioPacket

PARSE_ERRORS = (HEADER_CRC_ERROR, DATA_CRC_ERROR, MALFORMED_PACKET)

# (packet type, RORG or None for non-radio packets)
PacketKind = tuple[int, int | None]


def packet_kind(packet: Packet) -> PacketKind:
    return int(packet.packet_type), int(packet.rorg) if isinstance(packet, RadioPacket) else None


@dataclass(frozen=True)
class SenderStats:
    """What was last heard from one device (per-sender tracking must be enabled)."""

    packets: int
    last_seen_at: float
    rorg: int
    # Signal strength of the last packet, if the module reported it
    dbm: int | None


@dataclass(frozen=True)
class StatsSnapshot:
    """A consistent copy of the statistics at one point in time. Timestamps are `time.time()` values."""

    started_at: float
    packets_received: dict[PacketKind, int]
    packets_sent: dict[PacketKind, int]
    bytes_received: int
    bytes_sent: int
    parse_errors: dict[str, int]
    teach_in_responses: int
    base_id_requests: int
    base_id_timeouts: int
    base_id_fetch_seconds: float | None
    transport_errors: int
    processing_errors: int
    last_packet_received_at: float | None
    # Keyed by sender ID ('01:81:B7:44'); empty unless per-sender tracking is enabled
    senders: dict[str, SenderStats] = field(default_factory=dict)
    # Senders forgotten to stay within max_senders
    senders_evicted: int = 0


@dataclass
class CommunicatorStats:
    """Counters updated by the communicator thread; safe to read from any thread through snapshot()."""

    started_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _packets_received: Counter[PacketKind] = field(default_factory=Counter)
    _packets_sent: Counter[PacketKind] = field(default_factory=Counter)
    _bytes_received: int = 0
    _bytes_sent: int = 0
    _parse_errors: Counter[str] = field(default_factory=Counter)
    _teach_in_responses: int = 0
    _base_id_requests: int = 0
    _base_id_timeouts: int = 0
    _base_id_fetch_seconds: float | None = None
    _transport_errors: int = 0
    _processing_errors: int = 0
    _last_packet_received_at: float | None = None
    _max_senders: int = 0
    _senders: OrderedDict[str, SenderStats] = field(default_factory=OrderedDict)
    _senders_evicted: int = 0

    def enable_sender_tracking(self, max_senders: int = 500) -> None:
        """
        Also keep per-device statistics, for up to max_senders devices (the least recently heard ones are forgotten
        beyond that, so neighbours' devices picked up by the radio can't grow memory or metric cardinality forever).
        """
        with self._lock:
            self._max_senders = max_senders

    def record_bytes_received(self, count: int) -> None:
        with self._lock:
            self._bytes_received += count

    def record_received(self, packet: Packet) -> None:
        now = time.time()
        with self._lock:
            self._packets_received[packet_kind(packet)] += 1
            self._last_packet_received_at = now
            if self._max_senders and isinstance(packet, RadioPacket):
                self._record_sender(packet, now)

    def _record_sender(self, packet: RadioPacket, now: float) -> None:
        sender = packet.sender_hex
        previous = self._senders.pop(sender, None)
        self._senders[sender] = SenderStats(
            packets=(previous.packets if previous else 0) + 1,
            last_seen_at=now,
            rorg=int(packet.rorg),
            dbm=packet.dBm if len(packet.optional) >= 6 else None,
        )
        while len(self._senders) > self._max_senders:
            self._senders.popitem(last=False)
            self._senders_evicted += 1

    def record_sent(self, packet: Packet, byte_count: int) -> None:
        with self._lock:
            self._packets_sent[packet_kind(packet)] += 1
            self._bytes_sent += byte_count

    def record_parse_error(self, kind: str) -> None:
        with self._lock:
            self._parse_errors[kind] += 1

    def record_teach_in_response(self) -> None:
        with self._lock:
            self._teach_in_responses += 1

    def record_base_id_request(self) -> None:
        with self._lock:
            self._base_id_requests += 1

    def record_base_id_received(self, seconds: float) -> None:
        with self._lock:
            self._base_id_fetch_seconds = seconds

    def record_base_id_timeout(self) -> None:
        with self._lock:
            self._base_id_timeouts += 1

    def record_transport_error(self) -> None:
        with self._lock:
            self._transport_errors += 1

    def record_processing_error(self) -> None:
        with self._lock:
            self._processing_errors += 1

    def snapshot(self) -> StatsSnapshot:
        with self._lock:
            return StatsSnapshot(
                started_at=self.started_at,
                packets_received=dict(self._packets_received),
                packets_sent=dict(self._packets_sent),
                bytes_received=self._bytes_received,
                bytes_sent=self._bytes_sent,
                parse_errors={kind: self._parse_errors[kind] for kind in PARSE_ERRORS},
                teach_in_responses=self._teach_in_responses,
                base_id_requests=self._base_id_requests,
                base_id_timeouts=self._base_id_timeouts,
                base_id_fetch_seconds=self._base_id_fetch_seconds,
                transport_errors=self._transport_errors,
                processing_errors=self._processing_errors,
                last_packet_received_at=self._last_packet_received_at,
                senders=dict(self._senders),
                senders_evicted=self._senders_evicted,
            )


@dataclass(frozen=True)
class Health:
    """State of a communicator, for liveness/readiness probes. `problems` explains why it is not healthy."""

    running: bool
    transport_ready: bool
    base_id_known: bool
    receive_queue_size: int
    transmit_queue_size: int
    # Seconds since the last received packet, or since the communicator was created if none was received yet
    seconds_since_last_packet: float
    problems: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return not self.problems
