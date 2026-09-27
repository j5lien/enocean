"""
EnOcean serial protocol (ESP3) and equipment profiles (EEP).

The public API is importable from here: `from enocean import SerialCommunicator, RadioPacket, RORG`.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

# Libraries must not emit logs unless the application configures logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from enocean.communicators import Communicator, SerialCommunicator, TCPCommunicator  # noqa: E402
from enocean.protocol.constants import EVENT_CODE, PACKET, PARSE_RESULT, RETURN_CODE, RORG  # noqa: E402
from enocean.protocol.eep import EEP, FieldValue  # noqa: E402
from enocean.protocol.packet import (  # noqa: E402
    EventPacket,
    Packet,
    RadioPacket,
    ResponsePacket,
    UTETeachInPacket,
)
from enocean.stats import CommunicatorStats, Health, SenderStats, StatsSnapshot  # noqa: E402

try:
    __version__ = version('enocean')
except PackageNotFoundError:  # pragma: no cover - running from a source tree without installing
    __version__ = '0+unknown'

__all__ = [
    'EEP',
    'EVENT_CODE',
    'PACKET',
    'PARSE_RESULT',
    'RETURN_CODE',
    'RORG',
    'Communicator',
    'CommunicatorStats',
    'EventPacket',
    'FieldValue',
    'Health',
    'Packet',
    'RadioPacket',
    'ResponsePacket',
    'SenderStats',
    'SerialCommunicator',
    'StatsSnapshot',
    'TCPCommunicator',
    'UTETeachInPacket',
    '__version__',
]
