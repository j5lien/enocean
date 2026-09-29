"""Communicator receiving ESP3 packets over TCP."""

import logging
import socket
from collections.abc import Callable
from typing import TYPE_CHECKING

from enocean.communicators.communicator import Communicator
from enocean.protocol.packet import Packet

if TYPE_CHECKING:
    from enocean.devices import DeviceRegistry


class TCPCommunicator(Communicator):
    """TCP server receiving ESP3 packets from clients, e.g. a serial-to-TCP bridge (see examples/serial_to_tcp.py).

    Receive-only: packets passed to send() (including UTE teach-in responses) are not transmitted anywhere. Clients are
    served one at a time.

    Args:
        host: Address to listen on ('' for all).
        port: TCP port to listen on.
        callback: See Communicator.
        teach_in: See Communicator.
        devices: See Communicator.
    """

    logger = logging.getLogger('enocean.communicators.TCPCommunicator')

    def __init__(
        self,
        host: str = '',
        port: int = 9637,
        callback: Callable[[Packet], None] | None = None,
        teach_in: bool = True,
        devices: 'DeviceRegistry | None' = None,
    ) -> None:
        super().__init__(callback, teach_in, devices)
        self.host = host
        self.port = port

    def run(self) -> None:
        """Thread body: accept clients and parse the bytes they send until stopped."""
        self.logger.info(
            'TCPCommunicator started on %s:%s', self.host, self.port, extra=self._log_fields('communicator_started')
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(5)
        self._transport_ready = True
        sock.settimeout(0.5)

        while not self._stop_flag.is_set():
            try:
                (client, addr) = sock.accept()
            except TimeoutError:
                continue
            client_address = '%s:%s' % addr[:2]
            self.logger.debug(
                'Client "%s" connected',
                client_address,
                extra={**self._log_fields('client_connected'), 'client': client_address},
            )
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
                    self.logger.exception(
                        'Error while processing received packets', extra={'event': 'processing_error'}
                    )
                    self.stats.record_processing_error()
            client.close()
            self.logger.debug(
                'Client "%s" disconnected',
                client_address,
                extra={**self._log_fields('client_disconnected'), 'client': client_address},
            )
        sock.close()
        self._transport_ready = False
        self.logger.info(
            'TCPCommunicator stopped on %s:%s', self.host, self.port, extra=self._log_fields('communicator_stopped')
        )

    def _log_fields(self, event: str) -> dict[str, object]:
        return {'event': event, 'transport': 'tcp', 'host': self.host, 'port': self.port}
