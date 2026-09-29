import logging

import enocean
from enocean.communicators.communicator import Communicator, packet_log_fields
from enocean.devices import Device, DeviceRegistry
from enocean.protocol import crc8
from enocean.protocol.constants import RORG
from enocean.protocol.eep import EEPId
from enocean.protocol.packet import Packet, RadioPacket

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
    assert warning.event == 'data_crc_error'
    assert warning.packet_type == 'RADIO_ERP1'
    assert warning.length == len(RADIO_FRAME)


def test_malformed_packet_carries_its_bytes(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    data, optional = [RORG.BS4, 0x01], [0x01]  # a 4BS telegram too short for its data and sender
    header = [0x00, len(data), len(optional), 0x01]
    Packet.parse_msg(bytearray([0x55] + header + [crc8.calc(header)] + data + optional + [crc8.calc(data + optional)]))

    [warning] = records(caplog, logging.WARNING)
    assert warning.event == 'malformed_packet'
    assert warning.packet_type == 'RADIO_ERP1'
    assert (warning.data, warning.optional) == ('A5:01', '01')


def test_received_packets_carry_structured_fields(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    com = Communicator()
    com._buffer.extend(RADIO_FRAME)

    com.parse()

    [received] = [r for r in records(caplog, logging.DEBUG) if r.getMessage().startswith('Received')]
    assert received.event == 'packet_received'
    assert received.sender == '01:81:B7:44'
    assert received.destination == 'FF:FF:FF:FF'
    assert received.rorg == 'BS4'
    assert received.packet_type == 'RADIO_ERP1'
    assert received.dbm == -45
    assert (received.status, received.repeater_count) == (0x00, 0)
    assert received.eep is None


def test_log_fields_match_to_dict():
    registry = DeviceRegistry([Device('01:81:B7:44', EEPId(0xA5, 0x02, 0x05), name='sensor')])
    packet = Packet.parse_msg(bytearray(RADIO_FRAME))[2]
    registry.decode(packet)

    fields = packet_log_fields(packet, 'packet_received')

    assert fields.pop('event') == 'packet_received'
    assert fields == {key: value for key, value in packet.to_dict().items() if key in fields}
    assert fields['eep'] == 'A5-02-05'


def test_sent_packets_carry_structured_fields(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    com = Communicator()
    com.send(RadioPacket.create(rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, EB='pressed'))

    com._get_from_send_queue()

    [sent] = [r for r in records(caplog, logging.DEBUG) if r.getMessage().startswith('Sending')]
    assert sent.event == 'packet_sent'
    assert sent.rorg == 'RPS'
    assert sent.eep == 'F6-02-02'
    assert sent.dbm is None


def test_unknown_profile_is_named(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    packet = Packet.parse_msg(bytearray(RADIO_FRAME))[2]

    assert not packet.select_eep(0x02, 0x7F)

    [warning] = records(caplog, logging.WARNING)
    assert warning.event == 'unknown_profile'
    assert warning.eep == 'A5-02-7F'
    assert warning.command is None


def test_unknown_field_is_named(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    RadioPacket.create(rorg=RORG.BS4, rorg_func=0x02, rorg_type=0x05, TMP=20, XYZ=1)

    [warning] = records(caplog, logging.WARNING)
    assert warning.event == 'unknown_field'
    assert warning.shortcut == 'XYZ'


def test_building_default_packets_does_not_warn(caplog):
    caplog.set_level(logging.DEBUG, logger='enocean')
    Packet(0x05, data=[0x08])  # e.g. the CO_RD_IDBASE request, without optional data

    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
