import logging
import socket
from collections.abc import Callable

from enocean.communicators.communicator import Communicator
from enocean.protocol.packet import Packet


class TCPCommunicator(Communicator):
    """
    TCP server receiving ESP3 packets from clients, e.g. a serial-to-TCP bridge (see examples/serial_to_tcp.py).
    Receive-only: packets passed to send() (including UTE teach-in responses) are not transmitted anywhere.
    """

    logger = logging.getLogger('enocean.communicators.TCPCommunicator')

    def __init__(
        self, host: str = '', port: int = 9637, callback: Callable[[Packet], None] | None = None, teach_in: bool = True
    ) -> None:
        super().__init__(callback, teach_in)
        self.host = host
        self.port = port

    def run(self) -> None:
        self.logger.info('TCPCommunicator started')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(5)
        sock.settimeout(0.5)

        while not self._stop_flag.is_set():
            try:
                (client, addr) = sock.accept()
            except TimeoutError:
                continue
            self.logger.debug('Client "%s" connected', addr)
            client.settimeout(0.5)
            while not self._stop_flag.is_set():
                try:
                    data = client.recv(2048)
                except TimeoutError:
                    break
                if not data:
                    break
                self._feed(data)
                try:
                    self.parse()
                except Exception:
                    # Most likely raised by the user's callback: keep serving, but with the full traceback
                    self.logger.exception('Error while processing received packets')
                    self.stats.record_processing_error()
            client.close()
            self.logger.debug('Client disconnected')
        sock.close()
        self.logger.info('TCPCommunicator stopped')
