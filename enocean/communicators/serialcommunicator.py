import logging
import time
from collections.abc import Callable

import serial

from enocean.communicators.communicator import Communicator
from enocean.protocol.packet import Packet


class SerialCommunicator(Communicator):
    """Serial port communicator class for EnOcean radio"""

    logger = logging.getLogger('enocean.communicators.SerialCommunicator')

    def __init__(self, port: str = '/dev/ttyAMA0', callback: Callable[[Packet], None] | None = None) -> None:
        super().__init__(callback)
        # Initialize serial port
        self.__ser = serial.Serial(port, 57600, timeout=0.1)
        self._transport_ready = True

    def run(self) -> None:
        self.logger.info('SerialCommunicator started')
        while not self._stop_flag.is_set():
            # If there's messages in transmit queue
            # send them
            while True:
                packet = self._get_from_send_queue()
                if not packet:
                    break
                data = bytearray(packet.build())
                try:
                    self.__ser.write(data)
                except serial.SerialException:
                    self.logger.error('Serial port exception while writing! (device disconnected?)')
                    self.stats.record_transport_error()
                    self._transport_ready = False
                    self.stop()
                else:
                    self.stats.record_sent(packet, len(data))

            # Read chars from serial port as hex numbers
            try:
                self._feed(self.__ser.read(16))
            except serial.SerialException:
                self.logger.error('Serial port exception! (device disconnected or multiple access on port?)')
                self.stats.record_transport_error()
                self._transport_ready = False
                self.stop()

            try:
                self.parse()
            except Exception:
                # Most likely raised by the user's callback: keep running, but with the full traceback
                self.logger.exception('Error while processing received packets')
                self.stats.record_processing_error()

            time.sleep(0)

        self.__ser.close()
        self._transport_ready = False
        self.logger.info('SerialCommunicator stopped')
