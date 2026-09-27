"""Helpers for the hardware tests (fixtures are in conftest.py)."""

import os
import queue
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from enocean.communicators import SerialCommunicator
from enocean.protocol.packet import Packet

ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


def load_config() -> dict[str, str]:
    """KEY=VALUE lines from .env (comments and blank lines ignored), overridden by the environment."""
    config = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.split(' #', 1)[0].strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('\'"')
    config.update({key: value for key, value in os.environ.items() if key.startswith('ENOCEAN_')})
    return config


class Radio:
    """Waits for packets received by the communicator."""

    def __init__(self, communicator: SerialCommunicator, timeout: float) -> None:
        self.communicator = communicator
        self.timeout = timeout

    def drain(self) -> None:
        while not self.communicator.receive.empty():
            self.communicator.receive.get_nowait()

    def wait_for(self, predicate: Callable[[Packet], bool], timeout: float | None = None) -> Packet:
        timeout = self.timeout if timeout is None else timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                packet = self.communicator.receive.get(timeout=0.2)
            except queue.Empty:
                continue
            if predicate(packet):
                return packet
        pytest.fail('No matching packet within %ss' % timeout)


def device_id(config: dict[str, str], key: str) -> str:
    value = config.get(key)
    if not value:
        pytest.skip('%s is not configured in .env' % key)
    return value.upper()
