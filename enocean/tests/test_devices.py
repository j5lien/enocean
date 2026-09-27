import pytest

from enocean import PACKET, RORG, Communicator, EEPId, Packet, RadioPacket
from enocean.devices import Device, DeviceRegistry, device_id
from enocean.protocol import crc8

OPTIONAL = [0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x3A, 0x00]
SWITCH = [0x00, 0x37, 0x7E, 0x06]
LIGHT = [0x05, 0x99, 0x77, 0xAF]
NEIGHBOUR = [0xFF, 0xE8, 0x06, 0x02]


def frame(data, optional=OPTIONAL, packet_type=PACKET.RADIO_ERP1):
    header = [(len(data) >> 8) & 0xFF, len(data) & 0xFF, len(optional), packet_type]
    body = list(data) + list(optional)
    return bytes([0x55] + header + [crc8.calc(header)] + body + [crc8.calc(body)])


SWITCH_PRESSED = frame([RORG.RPS, 0x10] + SWITCH + [0x30])
LIGHT_OFF = frame([RORG.VLD, 0x04, 0x61, 0x80] + LIGHT + [0x00])
NEIGHBOUR_TELEGRAM = frame([RORG.RPS, 0x30] + NEIGHBOUR + [0x30])


@pytest.fixture
def registry():
    return DeviceRegistry.from_config(
        {
            '00:37:7e:06': {'eep': 'F6-02-02', 'name': 'Office switch', 'room': 'office'},
            # The format of enocean-sniffer's KNOWN_DEVICES
            '05:99:77:AF': {'rorg': RORG.VLD, 'func': 0x01, 'type': 0x12},
        },
        ignored=['ff:e8:06:02'],
    )


def parse(raw):
    return Packet.parse_msg(bytearray(raw))[2]


def test_device_ids_are_normalized():
    assert device_id('05:99:77:af ') == '05:99:77:AF'
    assert device_id(LIGHT) == '05:99:77:AF'


def test_from_config(registry):
    switch = registry.get('00:37:7E:06')
    assert switch == Device('00:37:7E:06', EEPId(0xF6, 0x02, 0x02), 'Office switch', {'room': 'office'})
    assert registry.get(LIGHT).eep == EEPId(0xD2, 0x01, 0x12)
    assert LIGHT in registry and '05:99:77:af' in registry and 'FF:FF:FF:FF' not in registry
    assert len(registry) == 2 and {d.id for d in registry} == {'00:37:7E:06', '05:99:77:AF'}
    assert registry.is_ignored(NEIGHBOUR)


def test_decode_known_device(registry):
    packet = parse(LIGHT_OFF)

    device = registry.decode(packet)

    assert device is registry.get(LIGHT) and packet.device is device
    assert packet.eep_id == EEPId(0xD2, 0x01, 0x12) and packet.command == 4
    assert packet.parsed['OV']['value'] == 'Output value 0% or OFF'
    assert packet.to_dict()['device'] == {'id': '05:99:77:AF', 'eep': 'D2-01-12', 'name': '', 'metadata': {}}


def test_decode_unknown_device_with_and_without_default(registry):
    unknown_switch = frame([RORG.RPS, 0x10, 0x00, 0x37, 0x00, 0x01, 0x30])

    packet = parse(unknown_switch)
    assert registry.decode(packet) is None
    assert packet.parsed == {} and packet.device is None

    registry.defaults[RORG.RPS] = EEPId.parse('F6-02-02')
    packet = parse(unknown_switch)
    assert registry.decode(packet) is None
    assert packet.parsed['EB']['value'] == 'pressed'


def test_profile_of_another_rorg_is_not_applied():
    registry = DeviceRegistry([Device('00:37:7E:06', EEPId.parse('A5-02-05'))])
    packet = parse(SWITCH_PRESSED)
    registry.decode(packet)
    assert packet.parsed == {}


def test_non_radio_and_teach_in_packets_are_left_alone(registry):
    response = parse(frame([0x00, 0xFF, 0x87, 0xCA, 0x00], [], PACKET.RESPONSE))
    assert registry.decode(response) is None
    teach_in = RadioPacket(PACKET.RADIO_ERP1, [0xD4, 0xA0, 0xFF, 0x3E, 0, 1, 1, 0xD2] + LIGHT + [0], OPTIONAL)
    assert registry.decode(parse(frame(teach_in.data))) is None


def test_add_remove_ignore():
    registry = DeviceRegistry()
    registry.add(Device('05:99:77:af', EEPId.parse('D2-01-12')))
    assert registry.get(LIGHT).id == '05:99:77:af'
    registry.remove(LIGHT)
    assert registry.get(LIGHT) is None
    registry.ignore(LIGHT)
    assert registry.is_ignored('05:99:77:AF')


def test_communicator_decodes_and_drops_ignored_devices(registry):
    received = []
    com = Communicator(callback=received.append, devices=registry)
    com._feed(SWITCH_PRESSED + NEIGHBOUR_TELEGRAM + LIGHT_OFF)

    com.parse()

    assert [p.sender_hex for p in received] == ['00:37:7E:06', '05:99:77:AF']
    assert received[0].device.name == 'Office switch'
    assert received[0].parsed['EB']['value'] == 'pressed'
    assert received[1].parsed['OV']['value'] == 'Output value 0% or OFF'
    snapshot = com.stats.snapshot()
    assert snapshot.packets_ignored == 1
    assert sum(snapshot.packets_received.values()) == 3
