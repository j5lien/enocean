import json

import pytest

from enocean import PACKET, EventPacket, Packet, RadioPacket, ResponsePacket
from enocean.protocol import crc8
from enocean.protocol.eep import EEPId


def frame(packet_type, data, optional=()):
    header = [(len(data) >> 8) & 0xFF, len(data) & 0xFF, len(optional), packet_type]
    body = list(data) + list(optional)
    return bytearray([0x55] + header + [crc8.calc(header)] + body + [crc8.calc(body)])


def parse(raw):
    return Packet.parse_msg(raw)[2]


def test_eep_id():
    assert EEPId.parse('D2-01-12') == EEPId(0xD2, 0x01, 0x12)
    assert EEPId.parse('d2:01:12') == EEPId(0xD2, 0x01, 0x12)
    assert str(EEPId(0xA5, 0x02, 0x05)) == 'A5-02-05'
    assert EEPId.parse(EEPId(0xF6, 2, 2)) == EEPId(0xF6, 2, 2)
    with pytest.raises(ValueError):
        EEPId.parse('D2-01')


def test_decoded_radio_packet():
    # The office light reporting channel 1 off (D2-01-12, command 4)
    packet = parse(
        frame(PACKET.RADIO_ERP1, [0xD2, 0x04, 0x61, 0x80, 0x05, 0x99, 0x77, 0xAF, 0x00], [1, 255, 255, 255, 255, 73, 0])
    )
    packet.parse_eep(0x01, 0x12)

    result = packet.to_dict()

    assert json.loads(json.dumps(result)) == result
    assert result['packet_type'] == 'RADIO_ERP1'
    assert result['rorg'] == 'VLD'
    assert result['sender'] == '05:99:77:AF'
    assert result['destination'] == 'FF:FF:FF:FF'
    assert result['dbm'] == -73
    assert result['eep'] == 'D2-01-12'
    assert result['command'] == 4
    assert result['data'] == 'D2:04:61:80:05:99:77:AF:00'
    assert result['received'].endswith('+00:00')
    assert result['values']['OV'] == {
        'description': 'Output value',
        'unit': '',
        'value': 'Output value 0% or OFF',
        'raw_value': 0,
    }
    assert packet.eep_id == EEPId(0xD2, 0x01, 0x12)


def test_undecoded_packet_has_no_eep():
    packet = parse(frame(PACKET.RADIO_ERP1, [0xF6, 0x10, 0x00, 0x37, 0x7E, 0x06, 0x30], []))
    result = packet.to_dict()
    assert result['eep'] is None and result['values'] == {} and result['dbm'] is None


def test_unknown_values_do_not_raise():
    radio = RadioPacket(PACKET.RADIO_ERP1, [0x62, 0x01, 0x01, 0x02, 0x03, 0x04, 0x00], [])
    assert radio.to_dict()['rorg'] == '0x62'
    assert Packet(0x33, [0x01]).to_dict()['packet_type'] == '0x33'
    assert ResponsePacket(PACKET.RESPONSE, [0x7F]).to_dict()['return_code'] == '0x7F'


def test_response_packet():
    packet = parse(frame(PACKET.RESPONSE, [0x00, 0xFF, 0x87, 0xCA, 0x00]))
    assert packet.to_dict() | {'received': None} == {
        'packet_type': 'RESPONSE',
        'received': None,
        'data': '00:FF:87:CA:00',
        'optional': '',
        'return_code': 'OK',
        'response_data': 'FF:87:CA:00',
    }


def test_event_packet():
    result = EventPacket(PACKET.EVENT, [0x02, 0x01]).to_dict()
    assert result['event_code'] == 'SA_CONFIRM_LEARN'
    assert result['event_data'] == '01'


def test_ute_teach_in_packet():
    packet = parse(
        frame(
            PACKET.RADIO_ERP1,
            [0xD4, 0xA0, 0xFF, 0x3E, 0x00, 0x01, 0x01, 0xD2, 0x01, 0x94, 0xE3, 0xB9, 0x00],
            [0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x40, 0x00],
        )
    )
    result = packet.to_dict()
    assert result['rorg'] == 'UTE'
    assert result['eep'] == 'D2-01-01'
    assert result['teach_in'] == {
        # DB6 bits 5-4 = 0b10: teach-in or deletion, left to the actuator
        'request': 'not_specific',
        'bidirectional': True,
        'response_expected': True,
        'number_of_channels': 0xFF,
        'manufacturer': 0x3E,
    }
