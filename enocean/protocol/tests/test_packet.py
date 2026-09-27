import datetime

import pytest

from enocean.protocol.constants import EVENT_CODE, PACKET, PARSE_RESULT, RORG
from enocean.protocol.packet import EventPacket, Packet, RadioPacket


def test_packet_examples():
    """Tests examples found at EnOceanSerialProtocol3.pdf / 74"""
    # fmt: off
    telegram_examples = {
        # Radio VLD
        PACKET.RADIO_ERP1: {
            'msg': bytearray([
                0x55,
                0x00, 0x0F, 0x07, 0x01,
                0x2B,
                0xD2, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x80, 0x35, 0xC4, 0x00,
                0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0x4D, 0x00,
                0x36]),
            'data_len': 15,
            'opt_len': 7,
        },
        # CO_WR_SLEEP
        PACKET.COMMON_COMMAND: {
            'msg': bytearray([
                0x55,
                0x00, 0x05, 0x00, 0x05,
                0xDB,
                0x01, 0x00, 0x00, 0x00, 0x0A,
                0x54]),
            'data_len': 5,
            'opt_len': 0,
        },
        # CO_WR_RESET
        PACKET.COMMON_COMMAND: {
            'msg': bytearray([
                0x55,
                0x00, 0x01, 0x00, 0x05,
                0x70,
                0x02,
                0x0E]),
            'data_len': 1,
            'opt_len': 0,
        },
        # CO_RD_IDBASE
        PACKET.COMMON_COMMAND: {
            'msg': bytearray([
                0x55,
                0x00, 0x01, 0x00, 0x05,
                0x70,
                0x08,
                0x38]),
            'data_len': 1,
            'opt_len': 0,
        },
        # Response RET_OK
        PACKET.RESPONSE: {
            'msg': bytearray([
                0x55,
                0x00, 0x05, 0x00, 0x02,
                0xCE,
                0x00, 0xFF, 0x80, 0x00, 0x00,
                0xDA]),
            'data_len': 5,
            'opt_len': 0,
        },
        # REMOTE_MAN_COMMAND
        PACKET.REMOTE_MAN_COMMAND: {
            'msg': bytearray([
                0x55,
                0x00, 0x19, 0x00, 0x07, 0x8D,
                0x12, 0x12, 0x07, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
                0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
                0xDA]),
            'data_len': 25,
            'opt_len': 0,
        },
        # QueryID
        PACKET.REMOTE_MAN_COMMAND: {
            'msg': bytearray([
                0x55,
                0x00, 0x0C, 0x00, 0x07,
                0xEF,
                0x00, 0x04, 0x07, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00,
                0x65]),
            'data_len': 12,
            'opt_len': 0,
        },
        # Custom test, containing 0x55 in message
        PACKET.RESPONSE: {
            'msg': bytearray([
                0x55,
                0x00, 0x05, 0x01, 0x02,
                0xDB,
                0x00, 0xFF, 0x9E, 0x55, 0x00,
                0x0A,
                0x79,
                # unnecessary data, to check for message length checking
                0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
            ]),
            'data_len': 5,
            'opt_len': 1,
        },
    }
    # fmt: on

    for packet, values in telegram_examples.items():
        status, remainder, pack = Packet.parse_msg(values['msg'])
        assert status == PARSE_RESULT.OK
        assert pack.packet_type != 0x00
        assert pack.packet_type == packet
        assert len(pack.data) == values['data_len']
        assert len(pack.optional) == values['opt_len']
        assert pack.status == 0x00
        assert pack.repeater_count == 0


def test_packet_fails():
    """
    Tests designed to fail.
    These include changes to checksum, data length or something like that.
    """
    # fmt: off
    fail_examples = (
        bytearray([
            0x55,
            0x00, 0x0F, 0x07, 0x01,
            0x2B,
            0xD2, 0xDD, 0xDC, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x80, 0x35, 0xC4, 0x00,
            0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0x4D, 0x00,
            0x36
        ]),
        bytearray([
            0x55,
            0x00, 0x0F, 0x07, 0x01,
            0x2B,
            0xD2, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x80, 0x35, 0xC4, 0x00,
            0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0x4D, 0x00,
            0x37
        ]),
        bytearray([
            0x55,
            0x00, 0x0F, 0x07, 0x01,
            0x1B,
            0xD2, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0x00, 0x80, 0x35, 0xC4, 0x00,
            0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0x4D, 0x00,
            0x36
        ]),
        bytearray([
            0x55,
            0x00, 0x01, 0x00, 0x05,
            0x70,
            0x38
        ]),
        bytearray([
            0x55,
            0x00, 0x01
        ]),
    )
    # fmt: on

    for msg in fail_examples:
        status, remainder, packet = Packet.parse_msg(msg)
        assert status in [PARSE_RESULT.INCOMPLETE, PARSE_RESULT.CRC_MISMATCH]


def test_packet_equals():
    # fmt: off
    data_1 = bytearray([
        0x55,
        0x00, 0x01, 0x00, 0x05,
        0x70,
        0x08,
        0x38
    ])
    data_2 = bytearray([
        0x55,
        0x00, 0x01, 0x00, 0x05,
        0x70,
        0x08,
        0x38
    ])
    # fmt: on
    _, _, packet_1 = Packet.parse_msg(data_1)
    _, _, packet_2 = Packet.parse_msg(data_2)

    assert str(packet_1) == '0x%02X %s %s %s' % (
        packet_1.packet_type,
        [hex(o) for o in packet_1.data],
        [hex(o) for o in packet_1.optional],
        packet_1.parsed,
    )
    assert str(packet_1) == str(packet_2)
    assert packet_1 == packet_2


def test_event_packet():
    # fmt: off
    data = bytearray([
        0x55,
        0x00, 0x01, 0x00, 0x04,
        0x77,
        0x01,
        0x07
    ])
    # fmt: on

    _, _, packet = Packet.parse_msg(data)
    assert isinstance(packet, EventPacket)
    assert packet.event == EVENT_CODE.SA_RECLAIM_NOT_SUCCESFUL
    assert packet.event_data == []
    assert packet.optional == []


def test_packet_accepts_bytes():
    for data in ([0x08], bytes([0x08]), bytearray([0x08]), (0x08,)):
        packet = Packet(PACKET.COMMON_COMMAND, data, bytearray([0x01]))
        assert packet.data == [0x08]
        assert packet.optional == [0x01]
    assert Packet(PACKET.COMMON_COMMAND).data == []


def test_packet_rejects_other_data_types():
    with pytest.raises(TypeError):
        Packet(PACKET.COMMON_COMMAND, 'not bytes')


def test_parsed_packets_are_timestamped_in_utc():
    before = datetime.datetime.now(datetime.timezone.utc)
    # fmt: off
    _, _, packet = Packet.parse_msg(bytearray([
        0x55, 0x00, 0x05, 0x00, 0x02, 0xCE, 0x00, 0xFF, 0x87, 0xCA, 0x00, 0xA3,
    ]))
    # fmt: on

    assert packet.received.tzinfo is datetime.timezone.utc
    assert before <= packet.received <= datetime.datetime.now(datetime.timezone.utc)
    assert Packet(PACKET.COMMON_COMMAND, [0x08]).received is None
    assert RadioPacket.create(rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, EB='pressed').received is None


def test_dbm_and_deprecated_dBm():  # noqa: N802
    packet = RadioPacket(PACKET.RADIO_ERP1, [RORG.RPS, 0x10, 1, 2, 3, 4, 0x30], [0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x3A, 0])
    assert packet.dbm == -58
    with pytest.warns(DeprecationWarning):
        assert packet.dBm == -58
    assert RadioPacket(PACKET.RADIO_ERP1, [RORG.RPS, 0x10, 1, 2, 3, 4, 0x30], []).dbm is None
