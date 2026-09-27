"""
Prometheus metrics for communicators. Requires the optional dependency: `pip install enocean[prometheus]`.

    from prometheus_client import start_http_server
    from enocean.prometheus import register

    register(communicator)          # or register({'usb0': com0, 'usb1': com1}), registry=..., namespace=...
    start_http_server(9100)

Metrics are computed from `communicator.stats` and `communicator.health()` when scraped: nothing is done between
scrapes.
"""

from collections.abc import Iterator, Mapping

try:
    from prometheus_client import REGISTRY, CollectorRegistry
    from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, Metric
    from prometheus_client.registry import Collector
except ImportError as error:  # pragma: no cover
    raise ImportError('enocean.prometheus requires prometheus-client: pip install "enocean[prometheus]"') from error

from enocean.communicators.communicator import Communicator
from enocean.protocol.constants import PACKET, RORG
from enocean.stats import PacketKind

# Readable label values; the enums' canonical names are legacy aliases for these two
_PACKET_TYPE_NAMES = {**{int(p): p.name.lower() for p in PACKET}, 0x01: 'radio_erp1', 0x0A: 'radio_erp2'}
_RORG_NAMES = {int(r): r.name.lower() for r in RORG}


def _packet_labels(kind: PacketKind) -> list[str]:
    packet_type, rorg = kind
    return [
        _PACKET_TYPE_NAMES.get(packet_type, '0x%02x' % packet_type),
        '' if rorg is None else _RORG_NAMES.get(rorg, '0x%02x' % rorg),
    ]


class EnOceanCollector(Collector):
    """
    Collects metrics from one communicator, or several given as {name: communicator} (adds a `communicator` label).

    namespace prefixes every metric name; const_labels are added to every sample (e.g. {'site': 'home'});
    max_silence (seconds) is passed to health() for the `healthy` gauge.
    """

    def __init__(
        self,
        communicators: Communicator | Mapping[str, Communicator],
        namespace: str = 'enocean',
        const_labels: Mapping[str, str] | None = None,
        max_silence: float | None = None,
    ) -> None:
        if isinstance(communicators, Communicator):
            self._communicators: dict[str, Communicator] = {'': communicators}
            self._communicator_label: list[str] = []
        else:
            self._communicators = dict(communicators)
            self._communicator_label = ['communicator']
        self._namespace = namespace
        self._const_labels = dict(const_labels or {})
        self._max_silence = max_silence

    def _labels(self, *names: str) -> list[str]:
        return list(self._const_labels) + self._communicator_label + list(names)

    def _values(self, name: str, *values: str) -> list[str]:
        return list(self._const_labels.values()) + ([name] if self._communicator_label else []) + list(values)

    def _counter(self, name: str, documentation: str, *labels: str) -> CounterMetricFamily:
        return CounterMetricFamily('%s_%s' % (self._namespace, name), documentation, labels=self._labels(*labels))

    def _gauge(self, name: str, documentation: str, *labels: str) -> GaugeMetricFamily:
        return GaugeMetricFamily('%s_%s' % (self._namespace, name), documentation, labels=self._labels(*labels))

    def collect(self) -> Iterator[Metric]:
        received = self._counter('packets_received', 'Packets received', 'packet_type', 'rorg')
        sent = self._counter('packets_sent', 'Packets sent', 'packet_type', 'rorg')
        bytes_received = self._counter('received_bytes', 'Bytes read from the transport')
        bytes_sent = self._counter('sent_bytes', 'Bytes written to the transport')
        parse_errors = self._counter(
            'parse_errors', 'Parse errors: header_crc (resynchronization), data_crc, malformed', 'kind'
        )
        teach_ins = self._counter('teach_in_responses', 'UTE teach-in responses sent')
        base_id_requests = self._counter('base_id_requests', 'Base ID requests sent to the module')
        base_id_timeouts = self._counter('base_id_timeouts', 'Base ID requests left unanswered')
        base_id_latency = self._gauge('base_id_fetch_seconds', 'Duration of the last successful base ID request')
        transport_errors = self._counter('transport_errors', 'Transport failures (e.g. serial read/write errors)')
        processing_errors = self._counter(
            'processing_errors', 'Exceptions raised while processing received packets (e.g. in callbacks)'
        )
        last_packet = self._gauge('last_packet_received_timestamp_seconds', 'Time of the last received packet')
        started = self._gauge('start_time_seconds', 'Time the communicator was created')
        up = self._gauge('up', '1 if the communicator thread is running and its transport is ready')
        healthy = self._gauge('healthy', '1 if communicator.health() reports no problem')
        base_id_known = self._gauge('base_id_known', '1 once the base ID of the module is known')
        queue_size = self._gauge('queue_size', 'Packets waiting in the receive/transmit queues', 'queue')

        for name, communicator in self._communicators.items():
            snapshot = communicator.stats.snapshot()
            health = communicator.health(self._max_silence)
            values = self._values(name)
            for kind, count in snapshot.packets_received.items():
                received.add_metric(values + _packet_labels(kind), count)
            for kind, count in snapshot.packets_sent.items():
                sent.add_metric(values + _packet_labels(kind), count)
            bytes_received.add_metric(values, snapshot.bytes_received)
            bytes_sent.add_metric(values, snapshot.bytes_sent)
            for kind_name, count in snapshot.parse_errors.items():
                parse_errors.add_metric(values + [kind_name], count)
            teach_ins.add_metric(values, snapshot.teach_in_responses)
            base_id_requests.add_metric(values, snapshot.base_id_requests)
            base_id_timeouts.add_metric(values, snapshot.base_id_timeouts)
            if snapshot.base_id_fetch_seconds is not None:
                base_id_latency.add_metric(values, snapshot.base_id_fetch_seconds)
            transport_errors.add_metric(values, snapshot.transport_errors)
            processing_errors.add_metric(values, snapshot.processing_errors)
            if snapshot.last_packet_received_at is not None:
                last_packet.add_metric(values, snapshot.last_packet_received_at)
            started.add_metric(values, snapshot.started_at)
            up.add_metric(values, float(health.running and health.transport_ready))
            healthy.add_metric(values, float(health.healthy))
            base_id_known.add_metric(values, float(health.base_id_known))
            queue_size.add_metric(values + ['receive'], health.receive_queue_size)
            queue_size.add_metric(values + ['transmit'], health.transmit_queue_size)

        yield from (
            received, sent, bytes_received, bytes_sent, parse_errors, teach_ins, base_id_requests, base_id_timeouts,
            base_id_latency, transport_errors, processing_errors, last_packet, started, up, healthy, base_id_known,
            queue_size,
        )  # fmt: skip


def register(
    communicators: Communicator | Mapping[str, Communicator],
    registry: CollectorRegistry = REGISTRY,
    namespace: str = 'enocean',
    const_labels: Mapping[str, str] | None = None,
    max_silence: float | None = None,
) -> EnOceanCollector:
    """Creates an EnOceanCollector and registers it (in the default registry unless one is given)."""
    collector = EnOceanCollector(communicators, namespace, const_labels, max_silence)
    registry.register(collector)
    return collector
