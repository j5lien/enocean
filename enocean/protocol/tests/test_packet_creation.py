import pytest

from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import Packet, RadioPacket


def test_packet_assembly():
    # fmt: off
    PACKET_CONTENT_1 = bytearray([
        0x55,
        0x00, 0x0A, 0x00, 0x01,
        0x80,
        0xA5, 0x00, 0x00, 0x00, 0x00, 0xDE, 0xAD, 0xBE, 0xEF, 0x00,
        0x18
    ])
    PACKET_CONTENT_2 = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x00, 0x00, 0xDE, 0xAD, 0xBE, 0xEF, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0xE4
    ])
    PACKET_CONTENT_3 = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x32, 0x20, 0x89, 0x00, 0xDE, 0xAD, 0xBE, 0xEF, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x43
    ])
    PACKET_CONTENT_4 = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x32, 0x00, 0x00, 0x00, 0xDE, 0xAD, 0xBE, 0xEF, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x80
    ])
    # fmt: on

    # manually assemble packet
    packet = Packet(PACKET.RADIO_ERP1)
    packet.rorg = RORG.BS4
    sender_bytes = [(0xDEADBEEF >> i & 0xFF) for i in (24, 16, 8, 0)]
    data = [0, 0, 0, 0]
    packet.data = [packet.rorg] + data + sender_bytes + [0]

    # test content
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(PACKET_CONTENT_1)
    assert list(packet_serialized) == list(PACKET_CONTENT_1)

    # set optional data
    sub_tel_num = 3
    destination = [255, 255, 255, 255]  # broadcast
    dbm = 0xFF
    security = 0
    packet.optional = [sub_tel_num] + destination + [dbm] + [security]

    # test content
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(PACKET_CONTENT_2)
    assert list(packet_serialized) == list(PACKET_CONTENT_2)

    # update data based on EEP
    packet.select_eep(0x20, 0x01, 1)
    prop = {
        'CV': 50,
        'TMP': 21.5,
        'ES': 'true',
    }
    packet.set_eep(prop)

    # test content
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(PACKET_CONTENT_3)
    assert list(packet_serialized) == list(PACKET_CONTENT_3)
    assert packet.rorg_func == 0x20
    assert packet.rorg_type == 0x01

    # Test the easier method of sending packets.
    packet = Packet.create(
        PACKET.RADIO_ERP1, rorg=RORG.BS4, rorg_func=0x20, rorg_type=0x01, learn=True, direction=1, **prop
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(PACKET_CONTENT_3)
    assert list(packet_serialized) == list(PACKET_CONTENT_3)
    assert packet.rorg_func == 0x20
    assert packet.rorg_type == 0x01

    # Test creating RadioPacket directly.
    packet = RadioPacket.create(rorg=RORG.BS4, rorg_func=0x20, rorg_type=0x01, learn=True, direction=2, SP=50)
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(PACKET_CONTENT_4)
    assert list(packet_serialized) == list(PACKET_CONTENT_4)
    assert packet.rorg_func == 0x20
    assert packet.rorg_type == 0x01


# Corresponds to the tests done in test_eep
def test_temperature():
    # fmt: off
    TEMPERATURE = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x5C
    ])
    # fmt: on
    packet = RadioPacket.create(
        rorg=RORG.BS4,
        rorg_func=0x02,
        rorg_type=0x05,
        sender=[0x01, 0x81, 0xB7, 0x44],
        TMP=26.66666666666666666666666666666666666666666667,
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(TEMPERATURE)
    assert list(packet_serialized) == list(TEMPERATURE)
    assert packet.learn is False

    # fmt: off
    TEMPERATURE = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x55, 0x00, 0x01, 0x81, 0xB7, 0x44, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0xE0
    ])
    # fmt: on
    packet = RadioPacket.create(
        rorg=RORG.BS4,
        rorg_func=0x02,
        rorg_type=0x05,
        sender=[0x01, 0x81, 0xB7, 0x44],
        learn=True,
        TMP=26.66666666666666666666666666666666666666666667,
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(TEMPERATURE)
    assert packet.learn is True


# Corresponds to the tests done in test_eep
def test_magnetic_switch():
    # fmt: off
    MAGNETIC_SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xD5, 0x08, 0x01, 0x82, 0x5D, 0xAB, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0xBA
    ])
    # fmt: on
    packet = RadioPacket.create(
        rorg=RORG.BS1, rorg_func=0x00, rorg_type=0x01, sender=[0x01, 0x82, 0x5D, 0xAB], CO='open'
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(MAGNETIC_SWITCH)
    assert list(packet_serialized) == list(MAGNETIC_SWITCH)
    assert packet.learn is False

    # fmt: off
    MAGNETIC_SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xD5, 0x00, 0x01, 0x82, 0x5D, 0xAB, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x06
    ])
    # fmt: on
    packet = RadioPacket.create(
        rorg=RORG.BS1, rorg_func=0x00, rorg_type=0x01, sender=[0x01, 0x82, 0x5D, 0xAB], learn=True, CO='open'
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(MAGNETIC_SWITCH)
    assert list(packet_serialized) == list(MAGNETIC_SWITCH)
    assert packet.learn is True

    # fmt: off
    MAGNETIC_SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xD5, 0x09, 0x01, 0x82, 0x5D, 0xAB, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x2E
    ])
    # fmt: on

    packet = RadioPacket.create(
        rorg=RORG.BS1, rorg_func=0x00, rorg_type=0x01, sender=[0x01, 0x82, 0x5D, 0xAB], CO='closed'
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(MAGNETIC_SWITCH)
    assert list(packet_serialized) == list(MAGNETIC_SWITCH)
    assert packet.learn is False

    # fmt: off
    MAGNETIC_SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xD5, 0x01, 0x01, 0x82, 0x5D, 0xAB, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x92
    ])
    # fmt: on

    packet = RadioPacket.create(
        rorg=RORG.BS1, rorg_func=0x00, rorg_type=0x01, sender=[0x01, 0x82, 0x5D, 0xAB], learn=True, CO='closed'
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(MAGNETIC_SWITCH)
    assert list(packet_serialized) == list(MAGNETIC_SWITCH)
    assert packet.learn is True


def test_switch():
    # fmt: off
    SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xF6, 0x50, 0x00, 0x29, 0x89, 0x79, 0x30,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x61
    ])
    # fmt: on

    # test also enum setting by integer value with EB0
    packet = RadioPacket.create(
        rorg=RORG.RPS,
        rorg_func=0x02,
        rorg_type=0x02,
        sender=[0x00, 0x29, 0x89, 0x79],
        SA='No 2nd action',
        EB=1,
        R1='Button BI',
        T21=True,
        NU=True,
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(SWITCH)
    assert list(packet_serialized) == list(SWITCH)

    # fmt: off
    SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xF6, 0x00, 0x00, 0x29, 0x89, 0x79, 0x20,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0xD2
    ])
    # fmt: on

    packet = RadioPacket.create(
        rorg=RORG.RPS,
        rorg_func=0x02,
        rorg_type=0x02,
        sender=[0x00, 0x29, 0x89, 0x79],
        SA='No 2nd action',
        EB='released',
        T21=True,
        NU=False,
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(SWITCH)
    assert list(packet_serialized) == list(SWITCH)


def test_illegal_eep_enum1():
    with pytest.raises(ValueError):
        RadioPacket.create(
            rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, sender=[0x00, 0x29, 0x89, 0x79], EB='inexisting'
        )


def test_illegal_eep_enum2():
    with pytest.raises(ValueError):
        RadioPacket.create(rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, sender=[0x00, 0x29, 0x89, 0x79], EB=2)


# Corresponds to the tests done in test_eep
def test_packets_with_destination():
    # fmt: off
    TEMPERATURE = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
        0x03, 0xDE, 0xAD, 0xBE, 0xEF, 0xFF, 0x00,
        0x5F
    ])
    # fmt: on
    packet = RadioPacket.create(
        rorg=RORG.BS4,
        rorg_func=0x02,
        rorg_type=0x05,
        sender=[0x01, 0x81, 0xB7, 0x44],
        destination=[0xDE, 0xAD, 0xBE, 0xEF],
        TMP=26.66666666666666666666666666666666666666666667,
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(TEMPERATURE)
    assert list(packet_serialized) == list(TEMPERATURE)
    assert packet.learn is False
    assert packet.sender_int == 25278276
    assert packet.destination_int == 3735928559

    # fmt: off
    MAGNETIC_SWITCH = bytearray([
        0x55,
        0x00, 0x07, 0x07, 0x01,
        0x7A,
        0xD5, 0x08, 0x01, 0x82, 0x5D, 0xAB, 0x00,
        0x03, 0xDE, 0xAD, 0xBE, 0xEF, 0xFF, 0x00,
        0xB9
    ])
    # fmt: on
    packet = RadioPacket.create(
        rorg=RORG.BS1,
        rorg_func=0x00,
        rorg_type=0x01,
        sender=[0x01, 0x82, 0x5D, 0xAB],
        destination=[0xDE, 0xAD, 0xBE, 0xEF],
        CO='open',
    )
    packet_serialized = packet.build()
    assert len(packet_serialized) == len(MAGNETIC_SWITCH)
    assert list(packet_serialized) == list(MAGNETIC_SWITCH)
    assert packet.learn is False


def test_vld():
    # fmt: off
    SWITCH = bytearray([
        0x55,
        0x00, 0x09, 0x07, 0x01,
        0x56,
        0xD2, 0x01, 0x1E, 0x64, 0xDE, 0xAD, 0xBE, 0xEF, 0x00,
        0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,
        0x5A
    ])
    # fmt: on
    packet = RadioPacket.create(rorg=RORG.VLD, rorg_func=0x01, rorg_type=0x01, command=1, DV=0, IO=0x1E, OV=0x64)
    packet_serialized = packet.build()

    assert len(packet_serialized) == len(SWITCH)
    assert list(packet_serialized) == list(SWITCH)
    assert packet.parsed['CMD']['raw_value'] == 0x01
    assert packet.parsed['IO']['raw_value'] == 0x1E
    assert packet.parsed['IO']['value'] == 'All output channels supported by the device'
    assert packet.parsed['DV']['value'] == 'Switch to new output value'
    assert packet.parsed['OV']['value'] == 'Output value 100% or ON'


def test_fails():
    with pytest.raises(ValueError):
        Packet.create(PACKET.RESPONSE, 0xA5, 0x01, 0x01)
    with pytest.raises(ValueError):
        Packet.create(PACKET.RADIO_ERP1, 0xA6, 0x01, 0x01)
    with pytest.raises(ValueError):
        Packet.create(PACKET.RADIO_ERP1, 0xA5, 0x01, 0x01, destination='ASDASDASD')
    with pytest.raises(ValueError):
        Packet.create(PACKET.RADIO_ERP1, 0xA5, 0x01, 0x01, sender='ASDASDASD')


def test_create_with_unknown_vld_profile():
    with pytest.raises(ValueError):
        RadioPacket.create(rorg=RORG.VLD, rorg_func=0x7F, rorg_type=0x7F)
