"""
Property-based tests for the ESP3 stream parser: whatever bytes come off the serial line (radio noise,
truncated or corrupted frames, arbitrary packet contents), parsing must never raise, must always make
progress, and must recover every valid frame that follows the garbage.
"""

import logging
import os

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from enocean.communicators.communicator import Communicator
from enocean.protocol import crc8
from enocean.protocol.constants import PACKET, PARSE_RESULT, RORG
from enocean.protocol.packet import Packet, RadioPacket

# Parsing garbage logs errors by design; keep test output readable
logging.getLogger('enocean').setLevel(logging.CRITICAL)

settings.register_profile('default', max_examples=300, suppress_health_check=[HealthCheck.too_slow])
# HYPOTHESIS_PROFILE=thorough for a longer local run
settings.register_profile('thorough', max_examples=6000, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile(os.environ.get('HYPOTHESIS_PROFILE', 'default'))

PACKET_TYPES = [int(p) for p in PACKET]
RORGS = [int(r) for r in RORG if r != RORG.UNDEFINED]


def frame(packet_type, data, optional):
    header = [(len(data) >> 8) & 0xFF, len(data) & 0xFF, len(optional), packet_type]
    body = list(data) + list(optional)
    return bytes([0x55] + header + [crc8.calc(header)] + body + [crc8.calc(body)])


@st.composite
def any_frames(draw):
    """CRC-valid frames with arbitrary type and contents, including ones too short for their type."""
    packet_type = draw(st.sampled_from(PACKET_TYPES) | st.integers(0, 255))
    data = draw(st.lists(st.integers(0, 255), max_size=20))
    if packet_type == PACKET.RADIO_ERP1 and data and draw(st.booleans()):
        data[0] = draw(st.sampled_from(RORGS))
    optional = draw(st.lists(st.integers(0, 255), max_size=10))
    return frame(packet_type, data, optional)


@st.composite
def radio_frames(draw):
    """Well-formed ERP1 radio telegrams, as a real module sends them."""
    rorg, payload_len = draw(st.sampled_from([(RORG.RPS, 1), (RORG.BS1, 1), (RORG.BS4, 4), (RORG.VLD, 6)]))
    payload = draw(st.lists(st.integers(0, 255), min_size=payload_len, max_size=payload_len))
    sender = draw(st.lists(st.integers(0, 255), min_size=4, max_size=4))
    status = draw(st.integers(0, 255))
    data = [int(rorg)] + payload + sender + [status]
    optional = [0x03, 0xFF, 0xFF, 0xFF, 0xFF, draw(st.integers(0, 255)), 0x00]
    return frame(PACKET.RADIO_ERP1, data, optional)


def corrupted_header():
    """A sync byte followed by a header whose CRC doesn't match (e.g. bit errors on the line)."""
    no_sync = st.integers(0, 255).filter(lambda b: b != 0x55)
    return (
        st.lists(no_sync, min_size=5, max_size=5)
        .filter(lambda h: crc8.calc(h[:4]) != h[4])
        .map(lambda h: bytes([0x55] + h))
    )


def noise():
    """Random bytes containing no sync byte."""
    return st.binary(max_size=30).map(lambda b: b.replace(b'\x55', b''))


def parse_stream(chunks):
    """Feeds chunks through a Communicator as a transport would, returns the packets it produced."""
    com = Communicator(teach_in=False)
    for chunk in chunks:
        com._buffer.extend(chunk)
        com.parse()
    packets = []
    while not com.receive.empty():
        packets.append(com.receive.get())
    return packets


@given(st.binary(max_size=200))
def test_parse_msg_never_raises_and_makes_progress(buf):
    status, remaining, packet = Packet.parse_msg(bytearray(buf))
    assert status in list(PARSE_RESULT)
    assert len(remaining) <= len(buf)
    if status != PARSE_RESULT.INCOMPLETE:
        # Otherwise the communicator's parse loop would spin forever
        assert len(remaining) < len(buf)
    assert (packet is not None) == (status == PARSE_RESULT.OK)


@given(any_frames())
def test_any_crc_valid_frame_is_returned_intact(raw):
    status, remaining, packet = Packet.parse_msg(bytearray(raw))
    assert status == PARSE_RESULT.OK
    assert remaining == []
    # Even when too short to be parsed for its type, no byte is lost
    assert bytes(packet.build()) == raw


@given(st.lists(any_frames() | st.binary(max_size=30), max_size=10))
def test_communicator_parse_terminates_on_any_stream(chunks):
    parse_stream(chunks)


@given(st.lists(radio_frames(), min_size=1, max_size=5), st.data())
def test_valid_frames_survive_arbitrary_chunking(frames, data):
    stream = b''.join(frames)
    cuts = sorted(data.draw(st.lists(st.integers(0, len(stream)), max_size=10)))
    chunks = [stream[a:b] for a, b in zip([0] + cuts, cuts + [len(stream)])]

    packets = parse_stream(chunks)

    assert [bytes(p.build()) for p in packets] == frames


@given(st.lists(st.tuples(noise(), corrupted_header() | st.just(b''), radio_frames()), min_size=1, max_size=5))
def test_resync_after_noise_and_corrupted_headers(segments):
    stream = b''.join(n + h + f for n, h, f in segments)
    assume(len(stream) < 500)

    packets = parse_stream([stream])

    assert [bytes(p.build()) for p in packets] == [f for _, _, f in segments]


@given(radio_frames(), st.lists(radio_frames(), min_size=1, max_size=3), st.data())
def test_resync_after_truncated_frame(truncated, frames, data):
    """Bytes lost mid-frame: the broken frame runs into the next ones, which must still be recovered."""
    cut = data.draw(st.integers(6, len(truncated) - 1))
    stream = truncated[:cut] + b''.join(frames)
    # Streams that are ambiguous by design, as CRC8 lets 1 in 256 corruptions through: the truncated
    # remains contain another sync byte, or the bytes the broken header claims happen to pass the data CRC.
    assume(0x55 not in truncated[1:cut])
    claimed_len = 6 + ((stream[1] << 8) | stream[2]) + stream[3] + 1
    assume(claimed_len > len(stream) or stream[claimed_len - 1] != crc8.calc(stream[6 : claimed_len - 1]))

    packets = parse_stream([stream])

    assert [bytes(p.build()) for p in packets] == frames


def test_radio_frame_without_optional_data():
    raw = frame(PACKET.RADIO_ERP1, [RORG.BS4, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00], [])

    status, _, packet = Packet.parse_msg(bytearray(raw))

    assert status == PARSE_RESULT.OK
    assert isinstance(packet, RadioPacket)
    assert packet.sender_hex == '01:81:B7:44'
    assert packet.destination_hex == 'FF:FF:FF:FF'
    assert packet.dBm == 0
    packet.parse_eep(0x02, 0x05)
    assert round(packet.parsed['TMP']['value'], 2) == 26.67


def test_too_short_radio_frame_is_returned_unparsed():
    raw = frame(PACKET.RADIO_ERP1, [RORG.BS4, 0x01], [])

    status, _, packet = Packet.parse_msg(bytearray(raw))

    assert status == PARSE_RESULT.OK
    assert type(packet) is Packet
    assert packet.data == [RORG.BS4, 0x01]
