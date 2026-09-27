"""EnOcean serial protocol (ESP3) and equipment profiles (EEP).

The public API is importable from here: `from enocean import SerialCommunicator, RadioPacket, RORG`.
"""

import logging

# Libraries must not emit logs unless the application configures logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

from enocean.actuators import BlindActuator, SwitchActuator  # noqa: E402
from enocean.communicators import Communicator, SerialCommunicator, TCPCommunicator  # noqa: E402
from enocean.devices import Device, DeviceRegistry  # noqa: E402
from enocean.protocol.constants import EVENT_CODE, PACKET, PARSE_RESULT, RETURN_CODE, RORG  # noqa: E402
from enocean.protocol.eep import EEP, EEPId, FieldDescription, FieldValue, ProfileDescription  # noqa: E402
from enocean.protocol.packet import (  # noqa: E402
    EventPacket,
    Packet,
    RadioPacket,
    ResponsePacket,
    UTETeachInPacket,
)
from enocean.stats import CommunicatorStats, Health, SenderStats, StatsSnapshot  # noqa: E402


def __getattr__(name: str) -> str:
    # __version__ is looked up on demand: importlib.metadata alone would double the import time
    if name == '__version__':
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version('enocean')
        except PackageNotFoundError:  # pragma: no cover - running from a source tree without installing
            return '0+unknown'
    raise AttributeError('module %r has no attribute %r' % (__name__, name))


__all__ = [
    'EEP',
    'BlindActuator',
    'EEPId',
    'EVENT_CODE',
    'PACKET',
    'PARSE_RESULT',
    'RETURN_CODE',
    'RORG',
    'Communicator',
    'CommunicatorStats',
    'Device',
    'DeviceRegistry',
    'EventPacket',
    'FieldDescription',
    'FieldValue',
    'Health',
    'Packet',
    'ProfileDescription',
    'RadioPacket',
    'ResponsePacket',
    'SenderStats',
    'SerialCommunicator',
    'StatsSnapshot',
    'SwitchActuator',
    'TCPCommunicator',
    'UTETeachInPacket',
    '__version__',
]
