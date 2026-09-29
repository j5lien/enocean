"""
Telegrams captured from real devices with a USB 300 stick (2026-09-27), checked against what the devices did.
Unlike the snapshot tests, these validate decoding against reality.
"""

import pytest

from enocean.protocol import crc8
from enocean.protocol.constants import PACKET, PARSE_RESULT, RORG
from enocean.protocol.packet import Packet, RadioPacket


def radio_frame(rorg, payload, sender, status, dbm):
    data = [rorg] + payload + sender + [status]
    optional = [0x01, 0xFF, 0xFF, 0xFF, 0xFF, -dbm, 0x00]
    header = [0x00, len(data), len(optional), PACKET.RADIO_ERP1]
    return bytes([0x55] + header + [crc8.calc(header)] + data + optional + [crc8.calc(data + optional)])


def decode(raw, func, type_, **kwargs):
    status, remaining, packet = Packet.parse_msg(bytearray(raw))
    assert status == PARSE_RESULT.OK and remaining == []
    assert isinstance(packet, RadioPacket)
    packet.parse_eep(func, type_, **kwargs)
    return packet, {shortcut: field['value'] for shortcut, field in packet.parsed.items()}


OFFICE_SWITCH = [0x00, 0x37, 0x7E, 0x06]  # PTM 210 wall switch, F6-02-02
OFFICE_LIGHT = [0x05, 0x99, 0x77, 0xAF]  # SIN-2-2-01 dual actuator, D2-01-12 (channel 1: office)
CONTROLLER = [0xFF, 0xF5, 0xB4, 0x80]  # another gateway commanding the actuator


@pytest.mark.parametrize(
    ('payload', 'status', 'expected'),
    [
        ([0x10], 0x30, {'R1': 0, 'EB': 1, 'SA': 0, 'T21': 1, 'NU': 1}),  # Button AI (I) pressed
        ([0x30], 0x30, {'R1': 1, 'EB': 1, 'SA': 0, 'T21': 1, 'NU': 1}),  # Button A0 (O) pressed
        ([0x00], 0x20, {'R1': 0, 'EB': 0, 'T21': 1, 'NU': 0}),  # released: the NU=0 variant, "no button"
    ],
    ids=['I-pressed', 'O-pressed', 'released'],
)
def test_ptm210_wall_switch(payload, status, expected):
    packet, values = decode(radio_frame(RORG.RPS, payload, OFFICE_SWITCH, status, -58), 0x02, 0x02)

    assert packet.sender_hex == '00:37:7E:06'
    assert packet.dbm == -58
    assert {shortcut: packet.parsed[shortcut]['raw_value'] for shortcut in expected} == expected
    assert values['EB'] == ('pressed' if expected['EB'] else 'released')
    if expected['NU']:
        assert values['R1'].startswith(('Button AI:', 'Button A0:')[expected['R1']])


@pytest.mark.parametrize(
    ('payload', 'output'),
    [([0x04, 0x61, 0xE4], 'Output value 1% to 100% or ON: 100'), ([0x04, 0x61, 0x80], 'Output value 0% or OFF')],
    ids=['on', 'off'],
)
def test_d2_01_12_actuator_status(payload, output):
    """The light's status report after the wall switch was pressed (I: on, O: off)."""
    packet, values = decode(radio_frame(RORG.VLD, payload, OFFICE_LIGHT, 0x00, -73), 0x01, 0x12, command=4)

    assert packet.sender_hex == '05:99:77:AF'
    assert packet.dbm == -73
    assert packet.command == 4
    assert values['IO'] == 'Output channel (to load): 1'
    assert values['OV'] == output
    assert values['LC'] == 'Local control enabled'


def test_d2_01_12_actuator_set_output():
    """A controller switching channel 1 on."""
    _, values = decode(radio_frame(RORG.VLD, [0x01, 0x01, 0x64], CONTROLLER, 0x00, -68), 0x01, 0x12, command=1)

    assert values == {
        'CMD': 'ID 01',
        'DV': 'Switch to new output value',
        'IO': 'Output channel (to load): 1',
        'OV': 'Output value 1% to 100% or ON: 100',
    }


def test_d2_01_12_same_command_we_would_send():
    """RadioPacket.create() builds the very payload the controller sent to switch the light on."""
    packet = RadioPacket.create(rorg=RORG.VLD, rorg_func=0x01, rorg_type=0x12, command=1, IO=1, OV=100)
    assert packet.data[1:4] == [0x01, 0x01, 0x64]


@pytest.mark.parametrize(
    ('payload', 'sender', 'expected'),
    [
        ([0x01, 0x01, 0x64], CONTROLLER, {'CMD': 'ID 01', 'DV': 'Switch to new output value'}),
        ([0x04, 0x61, 0xE4], OFFICE_LIGHT, {'CMD': 'ID 04', 'LC': 'Local control enabled'}),
    ],
    ids=['set-output', 'status'],
)
def test_d2_01_12_command_is_detected(payload, sender, expected):
    """Without command=, each telegram is decoded with its own command's layout."""
    _, values = decode(radio_frame(RORG.VLD, payload, sender, 0x00, -70), 0x01, 0x12)

    assert values.items() >= expected.items()
    assert values['OV'] == 'Output value 1% to 100% or ON: 100'


@pytest.mark.parametrize(
    ('data', 'status', 'repeater_count'),
    [
        ([0xD2, 0x01, 0x00, 0x64, 0xFF, 0xF5, 0xB4, 0x80, 0x81], 0x81, 1),
        ([0xD2, 0xFF, 0x00, 0x00, 0x04, 0x05, 0x97, 0x72, 0x22, 0x02], 0x02, 2),
        ([0xD2, 0x04, 0x60, 0xE4, 0x05, 0x97, 0xF5, 0x12, 0x00], 0x00, 0),
        ([0xA5, 0x00, 0x31, 0x00, 0x0B, 0xFF, 0xC9, 0x16, 0x92, 0x81], 0x81, 1),
        ([0xD4, 0xA0, 0xFF, 0x3E, 0x00, 0x01, 0x01, 0xD2, 0x01, 0x94, 0xE3, 0xB9, 0x81], 0x81, 1),
    ],
    ids=['vld-repeated-once', 'vld-repeated-twice', 'vld-direct', '4bs-repeated-once', 'ute-repeated-once'],
)
def test_status_and_repeater_count(data, status, repeater_count):
    """The status is the last data byte whatever the RORG, not the security level ending the optional data."""
    rorg, payload, sender = data[0], data[1:-5], data[-5:-1]
    status_, remaining, packet = Packet.parse_msg(bytearray(radio_frame(rorg, payload, sender, data[-1], -70)))
    assert status_ == PARSE_RESULT.OK and remaining == []

    assert packet.data == data
    assert packet.optional[-1] == 0x00
    assert packet.status == status
    assert packet.repeater_count == repeater_count
    assert packet.to_dict()['status'] == status
    assert packet.to_dict()['repeater_count'] == repeater_count
