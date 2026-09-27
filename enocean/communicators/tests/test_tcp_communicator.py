"""
End-to-end tests for TCPCommunicator: the real communicator thread listens on a local port and
clients push ESP3 frames to it over real sockets, as examples/serial_to_tcp.py does.
"""

import socket
import time

from enocean.communicators.tcpcommunicator import TCPCommunicator
from enocean.communicators.utils import send_to_tcp_socket
from enocean.protocol.constants import PACKET
from enocean.protocol.packet import Packet, RadioPacket

from conftest import BASE_ID_RESPONSE_FRAME, RADIO_FRAME, TIMEOUT


def connect(port):
    """Connects to the communicator, retrying while its thread is still binding the socket."""
    deadline = time.time() + TIMEOUT
    while True:
        try:
            return socket.create_connection(('127.0.0.1', port), timeout=TIMEOUT)
        except ConnectionRefusedError:
            if time.time() > deadline:
                raise
            time.sleep(0.02)


def test_frame_from_client_is_received(free_tcp_port, running):
    com = running(TCPCommunicator(host='127.0.0.1', port=free_tcp_port))

    client = connect(free_tcp_port)
    client.sendall(RADIO_FRAME)
    client.close()

    packet = com.receive.get(timeout=TIMEOUT)
    assert isinstance(packet, RadioPacket)
    assert packet.sender_hex == '01:81:B7:44'


def test_multiple_frames_in_one_connection(free_tcp_port, running):
    com = running(TCPCommunicator(host='127.0.0.1', port=free_tcp_port))

    client = connect(free_tcp_port)
    client.sendall(RADIO_FRAME + BASE_ID_RESPONSE_FRAME)
    client.close()

    types = [com.receive.get(timeout=TIMEOUT).packet_type for _ in range(2)]
    assert types == [PACKET.RADIO_ERP1, PACKET.RESPONSE]


def test_successive_clients(free_tcp_port, running):
    com = running(TCPCommunicator(host='127.0.0.1', port=free_tcp_port))

    for _ in range(3):
        client = connect(free_tcp_port)
        client.sendall(RADIO_FRAME)
        client.close()

    for _ in range(3):
        assert com.receive.get(timeout=TIMEOUT).sender_hex == '01:81:B7:44'


def test_send_to_tcp_socket_helper(free_tcp_port, running):
    """The serial -> TCP bridge helper delivers packets to a TCPCommunicator."""
    com = running(TCPCommunicator(host='127.0.0.1', port=free_tcp_port))
    connect(free_tcp_port).close()  # wait until listening
    _, _, packet = Packet.parse_msg(bytearray(RADIO_FRAME))

    send_to_tcp_socket('127.0.0.1', free_tcp_port, packet)

    assert com.receive.get(timeout=TIMEOUT).sender_hex == '01:81:B7:44'
