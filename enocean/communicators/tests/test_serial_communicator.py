"""
End-to-end tests for SerialCommunicator: the real communicator thread talks to a pseudo-terminal
acting as the EnOcean module (see conftest.py), so the whole path from raw serial bytes to decoded
packets (and from send() to bytes on the wire) is exercised.
"""

import os
import queue
import threading
import time

import pytest

from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import Packet, RadioPacket, UTETeachInPacket

from conftest import BASE_ID_RESPONSE_FRAME, RADIO_FRAME, TIMEOUT, UTE_TEACH_IN_FRAME


def test_radio_frame_is_received_and_decoded(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    module.write(RADIO_FRAME)

    packet = com.receive.get(timeout=TIMEOUT)
    assert isinstance(packet, RadioPacket)
    assert packet.rorg == RORG.BS4
    assert packet.sender_hex == '01:81:B7:44'
    assert packet.received is not None
    packet.parse_eep(0x02, 0x05)
    assert packet.parsed['TMP']['value'] == pytest.approx(26.67, abs=0.01)


def test_frame_split_across_serial_reads(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    for byte in RADIO_FRAME:
        module.write([byte])
        time.sleep(0.005)

    packet = com.receive.get(timeout=TIMEOUT)
    assert packet.sender_hex == '01:81:B7:44'
    assert com.receive.empty()


def test_back_to_back_frames_keep_order(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    module.write(RADIO_FRAME + BASE_ID_RESPONSE_FRAME + RADIO_FRAME)

    types = [com.receive.get(timeout=TIMEOUT).packet_type for _ in range(3)]
    assert types == [PACKET.RADIO_ERP1, PACKET.RESPONSE, PACKET.RADIO_ERP1]


def test_noise_before_frame_is_skipped(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    module.write(bytes([0x00, 0x12, 0xFF, 0x42]) + RADIO_FRAME)

    assert com.receive.get(timeout=TIMEOUT).sender_hex == '01:81:B7:44'


def test_callback_receives_packets_instead_of_queue(pty_port, running):
    module, port = pty_port
    received = queue.Queue()
    com = running(SerialCommunicator(port=port, callback=received.put))

    module.write(RADIO_FRAME)

    assert received.get(timeout=TIMEOUT).sender_hex == '01:81:B7:44'
    assert com.receive.empty()


def test_exception_in_callback_does_not_kill_communicator(pty_port, running):
    module, port = pty_port
    received = []

    def callback(packet):
        received.append(packet)
        if len(received) == 1:
            raise RuntimeError('boom')

    com = running(SerialCommunicator(port=port, callback=callback))

    module.write(RADIO_FRAME)
    deadline = time.time() + TIMEOUT
    while not received and time.time() < deadline:
        time.sleep(0.01)
    module.write(RADIO_FRAME)
    while len(received) < 2 and time.time() < deadline:
        time.sleep(0.01)

    assert len(received) == 2
    assert com.is_alive()


def test_sent_packet_is_written_to_serial(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))
    packet = RadioPacket.create(
        rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, sender=[0xDE, 0xAD, 0xBE, 0xEF], R1='Button AI', EB='pressed'
    )

    assert com.send(packet)

    written = module.read_packet()
    assert written.build() == packet.build()


def test_base_id_is_fetched_from_module(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))
    requests = []

    def answer_base_id_request():
        request = module.read_packet()
        requests.append(request)
        module.write(BASE_ID_RESPONSE_FRAME)

    responder = threading.Thread(target=answer_base_id_request, daemon=True)
    responder.start()

    assert com.base_id == [0xFF, 0x87, 0xCA, 0x00]

    responder.join(TIMEOUT)
    assert requests[0].packet_type == PACKET.COMMON_COMMAND
    assert requests[0].data == [0x08]  # CO_RD_IDBASE
    # The response is also left in the queue for the user
    assert com.receive.get(timeout=TIMEOUT).packet_type == PACKET.RESPONSE


def test_ute_teach_in_is_answered_automatically(pty_port, running):
    module, port = pty_port
    com = SerialCommunicator(port=port)
    com.base_id = [0xDE, 0xAD, 0xBE, 0xEF]
    running(com)

    module.write(UTE_TEACH_IN_FRAME)

    assert isinstance(com.receive.get(timeout=TIMEOUT), UTETeachInPacket)
    response = module.read_packet()
    assert response.rorg == RORG.UTE
    assert response.sender_hex == 'DE:AD:BE:EF'
    assert response.destination_hex == '01:94:E3:B9'


def test_ute_teach_in_is_ignored_when_disabled(pty_port, running):
    module, port = pty_port
    com = SerialCommunicator(port=port)
    com.base_id = [0xDE, 0xAD, 0xBE, 0xEF]
    com.teach_in = False
    running(com)

    module.write(UTE_TEACH_IN_FRAME)

    assert isinstance(com.receive.get(timeout=TIMEOUT), UTETeachInPacket)
    module.assert_silent()


def test_stop_ends_the_thread(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    com.stop()
    com.join(TIMEOUT)

    assert not com.is_alive()


def test_device_disconnect_stops_communicator(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))
    time.sleep(0.2)

    # Unplugging the module: the serial port starts failing on read
    os.close(module.fd)

    com.join(TIMEOUT)
    assert not com.is_alive()


def test_common_command_packet_roundtrip(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    com.send(Packet(PACKET.COMMON_COMMAND, data=[0x03]))  # CO_RD_VERSION

    written = module.read_packet()
    assert written.packet_type == PACKET.COMMON_COMMAND
    assert written.data == [0x03]


def answer_base_id_request(module):
    """Plays the module's side of CO_RD_IDBASE in the background."""

    def respond():
        request = module.read_packet()
        assert request.packet_type == PACKET.COMMON_COMMAND and request.data == [0x08]
        module.write(BASE_ID_RESPONSE_FRAME)

    responder = threading.Thread(target=respond, daemon=True)
    responder.start()
    return responder


def test_base_id_is_fetched_in_callback_mode(pty_port, running):
    module, port = pty_port
    received = queue.Queue()
    com = running(SerialCommunicator(port=port, callback=received.put))
    answer_base_id_request(module)

    assert com.base_id == [0xFF, 0x87, 0xCA, 0x00]
    # The response is still delivered to the callback
    assert received.get(timeout=TIMEOUT).packet_type == PACKET.RESPONSE


def test_base_id_fetch_keeps_other_packets_in_order(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    def respond():
        module.read_packet()
        module.write(RADIO_FRAME + RADIO_FRAME)
        time.sleep(0.2)
        module.write(BASE_ID_RESPONSE_FRAME)

    threading.Thread(target=respond, daemon=True).start()

    assert com.base_id == [0xFF, 0x87, 0xCA, 0x00]
    types = [com.receive.get(timeout=TIMEOUT).packet_type for _ in range(3)]
    assert types == [PACKET.RADIO_ERP1, PACKET.RADIO_ERP1, PACKET.RESPONSE]


def test_ute_teach_in_fetches_unknown_base_id_then_answers(pty_port, running):
    module, port = pty_port
    com = running(SerialCommunicator(port=port))

    module.write(UTE_TEACH_IN_FRAME)
    # The communicator doesn't know its base ID yet: it must ask the module first...
    request = module.read_packet()
    assert request.packet_type == PACKET.COMMON_COMMAND and request.data == [0x08]
    module.write(BASE_ID_RESPONSE_FRAME)

    # ...then answer the teach-in from that base ID, without losing the teach-in packet
    response = module.read_packet()
    assert response.rorg == RORG.UTE
    assert response.sender_hex == 'FF:87:CA:00'
    assert response.destination_hex == '01:94:E3:B9'
    assert isinstance(com.receive.get(timeout=TIMEOUT), UTETeachInPacket)
