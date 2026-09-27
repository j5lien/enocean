import logging

import enocean
from enocean.communicators.communicator import Communicator
from enocean.protocol.packet import Packet

# A5-02-05 temperature telegram from sender 01:81:B7:44
# fmt: off
RADIO_FRAME = bytes([
    0x55,
    0x00, 0x0A, 0x07, 0x01,
    0xEB,
    0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
    0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2D, 0x00,
    0x75,
])
# fmt: on


def records(caplog, level):
    return [r for r in caplog.records if r.name.startswith('enocean') and r.levelno == level]


def test_library_is_silent_unless_configured():
    assert any(isinstance(h, logging.NullHandler) for h in logging.getLogger(enocean.__name__).handlers)


def test_radio_noise_is_logged_at_debug_only(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    # Stray sync bytes followed by garbage: header CRC errors while resynchronizing
    Packet.parse_msg(bytearray([0x55, 0x01, 0x02, 0x03, 0x04, 0x05, 0x55, 0x10, 0x20, 0x30, 0x40, 0x50]))

    assert records(caplog, logging.DEBUG)
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_corrupted_telegram_is_a_warning(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    corrupted = bytearray(RADIO_FRAME)
    corrupted[-1] ^= 0xFF  # bad data CRC

    Packet.parse_msg(corrupted)

    [warning] = records(caplog, logging.WARNING)
    assert 'Data CRC error' in warning.getMessage()
    assert warning.packet_type == 0x01


def test_received_packets_carry_structured_fields(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    com = Communicator()
    com._buffer.extend(RADIO_FRAME)

    com.parse()

    [received] = [r for r in records(caplog, logging.DEBUG) if r.getMessage().startswith('Received')]
    assert received.sender == '01:81:B7:44'
    assert received.rorg == 0xA5
    assert received.packet_type == 0x01
    assert received.dbm == -45


def test_building_default_packets_does_not_warn(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    Packet(0x05, data=[0x08])  # e.g. the CO_RD_IDBASE request, without optional data

    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
