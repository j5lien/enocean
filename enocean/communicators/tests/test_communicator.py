import threading

from enocean.communicators.communicator import Communicator
from enocean.decorators import timing
from enocean.protocol.constants import PACKET
from enocean.protocol.packet import Packet, RadioPacket


@timing(1000)
def test_buffer():
    """Test buffer parsing for Communicator"""
    # fmt: off
    data = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
        0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2D, 0x00,
        0x75
    ])
    # fmt: on
    com = Communicator()
    com._buffer.extend(data[0:5])
    com.parse()
    assert com.receive.qsize() == 0
    com._buffer.extend(data[5:])
    com.parse()
    assert com.receive.qsize() == 1


@timing(1000)
def test_send():
    """Test sending packets to Communicator"""
    com = Communicator()
    assert com.send('AJSNDJASNDJANSD') is False
    assert com.transmit.qsize() == 0
    assert com._get_from_send_queue() is None
    assert com.send(Packet(PACKET.COMMON_COMMAND, [0x08])) is True
    assert com.transmit.qsize() == 1
    assert isinstance(com._get_from_send_queue(), Packet)


def test_stop():
    com = Communicator()
    com.stop()
    assert com._stop_flag.is_set()


def test_callback():
    def callback(packet):
        assert isinstance(packet, RadioPacket)

    # fmt: off
    data = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
        0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2D, 0x00,
        0x75
    ])
    # fmt: on

    com = Communicator(callback=callback)
    com._buffer.extend(data)
    com.parse()
    assert com.receive.qsize() == 0


def test_base_id():
    com = Communicator()
    assert com.base_id is None

    # fmt: off
    other_data = bytearray([
        0x55,
        0x00, 0x0A, 0x07, 0x01,
        0xEB,
        0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
        0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2D, 0x00,
        0x75
    ])
    # fmt: on

    # fmt: off
    response_data = bytearray([
        0x55,
        0x00, 0x05, 0x00, 0x02,
        0xCE,
        0x00, 0xFF, 0x87, 0xCA, 0x00,
        0xA3
    ])
    # fmt: on

    result = []
    requester = threading.Thread(target=lambda: result.append(com.base_id))
    requester.start()
    request = com.transmit.get(timeout=1)
    assert request.packet_type == PACKET.COMMON_COMMAND and request.data == [0x08]

    com._buffer.extend(other_data)
    com._buffer.extend(response_data)
    com.parse()
    requester.join(1)

    assert result == [[0xFF, 0x87, 0xCA, 0x00]]
    assert com.base_id == [0xFF, 0x87, 0xCA, 0x00]
    # Both packets are still delivered, in order
    assert [com.receive.get().packet_type for _ in range(2)] == [PACKET.RADIO_ERP1, PACKET.RESPONSE]


def test_base_id_times_out_without_response():
    com = Communicator()
    assert com.base_id is None
    # A later call sends a new request
    com.transmit.get_nowait()
    assert com.base_id is None
    assert com.transmit.qsize() == 1
