import pytest
from prometheus_client import CollectorRegistry, generate_latest

from enocean.communicators.communicator import Communicator
from enocean.prometheus import EnOceanCollector, register

# fmt: off
RADIO_FRAME = bytes([
    0x55,
    0x00, 0x0A, 0x07, 0x01,
    0xEB,
    0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
    0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2D, 0x00,
    0x75,
])
BASE_ID_RESPONSE_FRAME = bytes([0x55, 0x00, 0x05, 0x00, 0x02, 0xCE, 0x00, 0xFF, 0x87, 0xCA, 0x00, 0xA3])
# fmt: on


def communicator_with_traffic():
    com = Communicator()
    com._feed(RADIO_FRAME + RADIO_FRAME[:-1] + b'\x00' + BASE_ID_RESPONSE_FRAME)
    com.parse()
    return com


@pytest.fixture
def registry():
    return CollectorRegistry()


def test_metrics_of_one_communicator(registry):
    com = communicator_with_traffic()
    register(com, registry=registry)

    value = registry.get_sample_value
    assert value('enocean_packets_received_total', {'packet_type': 'radio_erp1', 'rorg': 'bs4'}) == 1
    assert value('enocean_packets_received_total', {'packet_type': 'response', 'rorg': ''}) == 1
    assert value('enocean_received_bytes_total') == 3 * len(RADIO_FRAME) - len(RADIO_FRAME) + len(
        BASE_ID_RESPONSE_FRAME
    )
    assert value('enocean_parse_errors_total', {'kind': 'data_crc'}) == 1
    assert value('enocean_parse_errors_total', {'kind': 'malformed'}) == 0
    assert value('enocean_last_packet_received_timestamp_seconds') > 0
    assert value('enocean_start_time_seconds') > 0
    # Not started: not up, not healthy
    assert value('enocean_up') == 0
    assert value('enocean_healthy') == 0
    assert value('enocean_base_id_known') == 0
    assert value('enocean_queue_size', {'queue': 'receive'}) == 2
    assert value('enocean_queue_size', {'queue': 'transmit'}) == 0
    # Only exported once known
    assert value('enocean_base_id_fetch_seconds') is None


def test_several_communicators_namespace_and_labels(registry):
    register(
        {'usb0': communicator_with_traffic(), 'usb1': Communicator()},
        registry=registry,
        namespace='home_enocean',
        const_labels={'site': 'home'},
    )

    value = registry.get_sample_value
    labels = {'site': 'home', 'packet_type': 'radio_erp1', 'rorg': 'bs4'}
    assert value('home_enocean_packets_received_total', {**labels, 'communicator': 'usb0'}) == 1
    assert value('home_enocean_packets_received_total', {**labels, 'communicator': 'usb1'}) is None
    assert value('home_enocean_received_bytes_total', {'site': 'home', 'communicator': 'usb1'}) == 0


def test_text_exposition(registry):
    registry.register(EnOceanCollector(communicator_with_traffic()))

    text = generate_latest(registry).decode()

    assert '# TYPE enocean_packets_received_total counter' in text
    assert 'enocean_packets_received_total{packet_type="radio_erp1",rorg="bs4"} 1.0' in text
    assert '# TYPE enocean_queue_size gauge' in text


def test_metrics_follow_the_communicator(registry):
    com = Communicator()
    register(com, registry=registry)
    assert registry.get_sample_value('enocean_received_bytes_total') == 0

    com._feed(RADIO_FRAME)
    com.parse()

    assert registry.get_sample_value('enocean_received_bytes_total') == len(RADIO_FRAME)


def test_per_sender_metrics_are_opt_in(registry):
    com = communicator_with_traffic()
    register(com, registry=registry)
    assert registry.get_sample_value('enocean_senders_evicted_total') is None


def test_per_sender_metrics(registry):
    com = Communicator()
    register(com, registry=registry, per_sender=True, max_senders=10)

    com._feed(RADIO_FRAME)
    com.parse()

    labels = {'sender': '01:81:B7:44', 'rorg': 'bs4'}
    assert registry.get_sample_value('enocean_sender_packets_received_total', labels) == 1
    assert registry.get_sample_value('enocean_sender_dbm', labels) == -45
    assert registry.get_sample_value('enocean_sender_last_seen_timestamp_seconds', labels) > 0
    assert registry.get_sample_value('enocean_senders_evicted_total') == 0
