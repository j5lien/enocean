import pytest

from enocean import Communicator
from enocean.actuators import ALL_CHANNELS, BlindActuator, SwitchActuator

BASE_ID = [0xFF, 0xC3, 0x6F, 0x80]


@pytest.fixture
def communicator():
    communicator = Communicator()
    communicator.base_id = BASE_ID
    return communicator


def sent(communicator):
    packet = communicator.transmit.get_nowait()
    return packet.data[1:-5], packet


def test_switch_turn_on_matches_a_real_controller(communicator):
    SwitchActuator(communicator, '05:99:77:AF').turn_on(channel=1)

    payload, packet = sent(communicator)
    # The payload captured from a controller switching the office light on (see test_real_frames.py)
    assert payload == [0x01, 0x01, 0x64]
    assert packet.sender_hex == 'FF:C3:6F:80'
    assert packet.optional[1:5] == [0x05, 0x99, 0x77, 0xAF]
    assert packet.dbm is None
    assert packet.to_dict()['dbm'] is None


def test_switch_commands(communicator):
    light = SwitchActuator(communicator, [0x05, 0x99, 0x77, 0xAF])

    light.turn_off(channel=0)
    assert sent(communicator)[0] == [0x01, 0x00, 0x00]
    light.set_output(50)
    payload, packet = sent(communicator)
    assert payload == [0x01, ALL_CHANNELS, 50]
    assert packet.parsed['IO']['value'] == 'All output channels supported by the device'
    light.query_status(channel=1)
    assert sent(communicator)[0] == [0x03, 0x01]


def test_switch_rejects_invalid_values(communicator):
    with pytest.raises(ValueError):
        SwitchActuator(communicator, '05:99:77:AF').set_output(101)


def test_blind_commands(communicator):
    cover = BlindActuator(communicator, '05:97:BA:73')

    cover.go_to(position=50)
    payload, packet = sent(communicator)
    assert payload == [50, 127, 0x00, 0x01]
    assert packet.parsed['POS']['value'] == 50.0 and packet.parsed['POS']['unit'] == '%'
    assert packet.parsed['ANG']['raw_value'] == 127  # do not change
    cover.go_to(angle=20)
    assert sent(communicator)[0] == [127, 20, 0x00, 0x01]
    cover.stop()
    assert sent(communicator)[0] == [0x02]
    cover.query_position()
    assert sent(communicator)[0] == [0x03]
    with pytest.raises(ValueError):
        cover.go_to(position=-1)


def test_sender_can_be_another_id_of_the_module(communicator):
    SwitchActuator(communicator, '05:99:77:AF', sender=[0xFF, 0xC3, 0x6F, 0x81]).turn_on()
    assert sent(communicator)[1].sender_hex == 'FF:C3:6F:81'


def test_unknown_base_id():
    communicator = Communicator()  # no module answers the base ID request (waits for it up to a second)
    with pytest.raises(RuntimeError):
        SwitchActuator(communicator, '05:99:77:AF').turn_on()
