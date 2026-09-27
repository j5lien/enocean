'''
Fixtures for end-to-end communicator tests.

A pseudo-terminal stands in for the EnOcean USB/serial module: the communicator opens the pty's
slave side as its serial port, while tests act as the radio module on the master side, writing raw
ESP3 frames in and reading what the communicator writes out.
'''
import os
import select
import socket
import sys
import time

import pytest

from enocean.protocol.constants import PARSE_RESULT
from enocean.protocol.packet import Packet

# A5-02-05 temperature telegram from sender 01:81:B7:44
RADIO_FRAME = bytes([
    0x55,
    0x00, 0x0A, 0x07, 0x01,
    0xEB,
    0xA5, 0x00, 0x00, 0x55, 0x08, 0x01, 0x81, 0xB7, 0x44, 0x00,
    0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2D, 0x00,
    0x75,
])

# UTE teach-in request (D2-01-01) from sender 01:94:E3:B9, expecting a response
UTE_TEACH_IN_FRAME = bytes([
    0x55,
    0x00, 0x0D, 0x07, 0x01,
    0xFD,
    0xD4, 0xA0, 0xFF, 0x3E, 0x00, 0x01, 0x01, 0xD2, 0x01, 0x94, 0xE3, 0xB9, 0x00,
    0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x40, 0x00,
    0xAB,
])

# RESPONSE RET_OK to CO_RD_IDBASE, base ID FF:87:CA:00
BASE_ID_RESPONSE_FRAME = bytes([
    0x55,
    0x00, 0x05, 0x00, 0x02,
    0xCE,
    0x00, 0xFF, 0x87, 0xCA, 0x00,
    0xA3,
])

# How long to wait for anything asynchronous before failing
TIMEOUT = 3


class FakeSerialModule:
    ''' The "radio module" end of the pty: writes frames to the communicator, reads frames it sends. '''

    def __init__(self, fd):
        self.fd = fd
        self._buffer = []

    def write(self, data):
        os.write(self.fd, bytes(data))

    def read_packet(self, timeout=TIMEOUT):
        ''' Returns the next complete, CRC-valid packet written by the communicator. '''
        deadline = time.time() + timeout
        while True:
            status, self._buffer, packet = Packet.parse_msg(self._buffer)
            if status == PARSE_RESULT.OK:
                return packet
            remaining = deadline - time.time()
            if remaining <= 0:
                raise AssertionError('No packet received from communicator within %ss' % timeout)
            ready, _, _ = select.select([self.fd], [], [], remaining)
            if ready:
                self._buffer.extend(os.read(self.fd, 1024))

    def assert_silent(self, duration=0.3):
        ready, _, _ = select.select([self.fd], [], [], duration)
        assert not ready, 'Communicator unexpectedly wrote %r' % os.read(self.fd, 1024)


@pytest.fixture
def pty_port():
    ''' Yields (FakeSerialModule, slave device path). '''
    if sys.platform == 'win32':
        pytest.skip('pseudo-terminals are not available on Windows')
    import tty
    master, slave = os.openpty()
    # Raw mode, so the line discipline doesn't translate or echo bytes
    tty.setraw(master)
    tty.setraw(slave)
    try:
        yield FakeSerialModule(master), os.ttyname(slave)
    finally:
        os.close(slave)
        try:
            os.close(master)
        except OSError:
            pass


@pytest.fixture
def free_tcp_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture
def running():
    ''' Starts communicators and guarantees they are stopped and joined after the test. '''
    started = []

    def start(communicator):
        communicator.daemon = True
        communicator.start()
        started.append(communicator)
        return communicator

    yield start

    for communicator in started:
        communicator.stop()
        communicator.join(TIMEOUT)
        assert not communicator.is_alive(), '%r did not stop' % communicator
