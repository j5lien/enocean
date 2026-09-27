"""Tests against a real EnOcean USB stick and real devices. Run with `make test-hardware` (see conftest.py)."""

import time

import pytest

from enocean.communicators import SerialCommunicator
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import Packet, RadioPacket, ResponsePacket
from enocean.utils import to_hex_string

from stick import Radio, device_id

pytestmark = pytest.mark.hardware


def test_base_id(communicator: SerialCommunicator) -> None:
    base_id = communicator.base_id
    assert base_id is not None
    # Base IDs are allocated in FF:80:00:00 - FF:FF:FF:80
    assert base_id[0] == 0xFF and base_id[1] >= 0x80
    assert communicator.stats.snapshot().base_id_timeouts == 0


def test_version(communicator: SerialCommunicator, radio: Radio, say) -> None:
    communicator.send(Packet(PACKET.COMMON_COMMAND, data=[0x03]))  # CO_RD_VERSION, local to the stick

    response = radio.wait_for(lambda p: isinstance(p, ResponsePacket) and len(p.response_data) >= 32, timeout=2)

    data = response.response_data
    description = bytes(data[16:32]).rstrip(b'\x00').decode(errors='replace')
    say('Stick: %s, app %d.%d.%d.%d, API %d.%d.%d.%d, chip %s' % (description, *data[0:8], to_hex_string(data[8:12])))
    assert description


def test_health(communicator: SerialCommunicator) -> None:
    health = communicator.health()
    assert health.healthy, health.problems
    assert health.transport_ready and health.base_id_known


def test_passive_listening(communicator: SerialCommunicator, config: dict[str, str], say) -> None:
    """Whatever the neighbourhood sends, the communicator keeps up without crashing or losing sync."""
    seconds = float(config.get('ENOCEAN_TEST_LISTEN_SECONDS', 15))
    start = time.time()
    before = communicator.stats.snapshot()
    time.sleep(seconds)
    after = communicator.stats.snapshot()

    received = sum(after.packets_received.values()) - sum(before.packets_received.values())
    devices = sum(1 for sender in after.senders.values() if sender.last_seen_at >= start)
    errors = {kind: after.parse_errors[kind] - before.parse_errors[kind] for kind in after.parse_errors}
    say('Heard %d packets from %d devices in %.0f s, parse errors: %s' % (received, devices, seconds, errors))
    assert after.processing_errors == 0
    assert after.transport_errors == 0
    assert communicator.health().healthy


@pytest.mark.interactive
def test_wall_switch_toggles_light(radio: Radio, config: dict[str, str], say) -> None:
    """Pressing both sides of the wall switch: its telegrams and the light's status reports are received and decoded."""
    switch = device_id(config, 'ENOCEAN_TEST_SWITCH')
    light = device_id(config, 'ENOCEAN_TEST_LIGHT')
    channel = int(config.get('ENOCEAN_TEST_LIGHT_CHANNEL', 0))
    outputs = []

    for side in ('I (top)', 'O (bottom)'):
        say('Press the %s side of wall switch %s' % (side, switch))
        press = radio.wait_for(lambda p: isinstance(p, RadioPacket) and p.sender_hex == switch)
        assert press.rorg == RORG.RPS
        press.parse_eep(0x02, 0x02)
        assert press.parsed['EB']['value'] == 'pressed'
        say('Switch: %s pressed (%d dBm)' % (press.parsed['R1']['value'], press.dBm))

        def is_light_status(p: Packet) -> bool:
            # D2-01-12 command 4 (actuator status response) for the configured channel
            return (
                isinstance(p, RadioPacket)
                and p.sender_hex == light
                and p.rorg == RORG.VLD
                and p.data[1] & 0x0F == 4
                and p.data[2] & 0x1F == channel
            )

        status = radio.wait_for(is_light_status, timeout=5)
        status.parse_eep(0x01, 0x12, command=4)
        say('Light %s channel %d: %s (%d dBm)' % (light, channel, status.parsed['OV']['value'], status.dBm))
        outputs.append(status.parsed['OV']['raw_value'])

    # One side switches on, the other off
    assert len(set(outputs)) == 2
