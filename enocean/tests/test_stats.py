import threading

from enocean.communicators.communicator import Communicator
from enocean.protocol import crc8
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import DATA_CRC_ERROR, HEADER_CRC_ERROR, MALFORMED_PACKET, Packet
from enocean.stats import CommunicatorStats

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


def frame(packet_type, data, optional=()):
    header = [(len(data) >> 8) & 0xFF, len(data) & 0xFF, len(optional), packet_type]
    body = list(data) + list(optional)
    return bytes([0x55] + header + [crc8.calc(header)] + body + [crc8.calc(body)])


def parse_errors(buf):
    errors = []
    Packet.parse_msg(bytearray(buf), on_error=errors.append)
    return errors


def test_parse_msg_reports_error_kinds():
    assert parse_errors(RADIO_FRAME) == []
    assert parse_errors(RADIO_FRAME[:2] + b'\x0b' + RADIO_FRAME[3:]) == [HEADER_CRC_ERROR]
    assert parse_errors(RADIO_FRAME[:-1] + b'\x00') == [DATA_CRC_ERROR]
    assert parse_errors(frame(PACKET.RADIO_ERP1, [RORG.BS4, 0x01])) == [MALFORMED_PACKET]


def test_empty_snapshot():
    snapshot = CommunicatorStats().snapshot()
    assert snapshot.packets_received == {}
    assert snapshot.parse_errors == {HEADER_CRC_ERROR: 0, DATA_CRC_ERROR: 0, MALFORMED_PACKET: 0}
    assert snapshot.last_packet_received_at is None
    assert snapshot.base_id_fetch_seconds is None


def test_communicator_counts_received_traffic():
    com = Communicator()
    noise = bytes([0x55, 0x01, 0x02, 0x03, 0x04, 0x05])
    corrupted = RADIO_FRAME[:-1] + b'\x00'

    malformed = frame(PACKET.RADIO_ERP1, [RORG.BS4, 0x01])

    com._feed(noise + RADIO_FRAME + corrupted + BASE_ID_RESPONSE_FRAME + malformed)
    com.parse()

    snapshot = com.stats.snapshot()
    assert snapshot.bytes_received == len(noise) + 2 * len(RADIO_FRAME) + len(BASE_ID_RESPONSE_FRAME) + len(malformed)
    assert snapshot.packets_received == {
        (PACKET.RADIO_ERP1, RORG.BS4): 1,
        (PACKET.RESPONSE, None): 1,
        # Malformed packets are still delivered, as plain Packets
        (PACKET.RADIO_ERP1, None): 1,
    }
    assert snapshot.parse_errors[DATA_CRC_ERROR] == 1
    assert snapshot.parse_errors[MALFORMED_PACKET] == 1
    # The noise and the corrupted frame's inner sync bytes each cost a header CRC error while resynchronizing
    assert snapshot.parse_errors[HEADER_CRC_ERROR] >= 1
    assert snapshot.last_packet_received_at is not None


def test_base_id_fetch_is_measured():
    com = Communicator()
    requester = threading.Thread(target=lambda: com.base_id)
    requester.start()
    com.transmit.get(timeout=1)
    com._feed(BASE_ID_RESPONSE_FRAME)
    com.parse()
    requester.join(1)

    snapshot = com.stats.snapshot()
    assert snapshot.base_id_requests == 1
    assert snapshot.base_id_timeouts == 0
    assert 0 <= snapshot.base_id_fetch_seconds < 1


def test_base_id_timeout_is_counted():
    com = Communicator()
    assert com.base_id is None

    snapshot = com.stats.snapshot()
    assert snapshot.base_id_requests == 1
    assert snapshot.base_id_timeouts == 1


def test_snapshot_is_a_copy():
    stats = CommunicatorStats()
    snapshot = stats.snapshot()
    stats.record_parse_error(HEADER_CRC_ERROR)
    assert snapshot.parse_errors[HEADER_CRC_ERROR] == 0
