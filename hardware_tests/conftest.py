"""
Fixtures for tests against a real EnOcean USB stick, configured in .env (see .env.example).

Skipped when the stick isn't configured or plugged in. Deselected by default (`hardware` marker): run them with
`make test-hardware`. They only listen: nothing is transmitted over the air, and UTE teach-in auto-answers are off.
"""

import os
from collections.abc import Callable, Iterator

import pytest

from enocean.communicators import SerialCommunicator

from stick import Radio, load_config


@pytest.fixture(scope='session')
def config() -> dict[str, str]:
    config = load_config()
    port = config.get('ENOCEAN_PORT')
    if not port:
        pytest.skip('ENOCEAN_PORT is not configured (copy .env.example to .env)')
    if not os.path.exists(port):
        pytest.skip('%s not found: is the EnOcean stick plugged in?' % port)
    return config


@pytest.fixture(scope='session')
def communicator(config: dict[str, str]) -> Iterator[SerialCommunicator]:
    communicator = SerialCommunicator(port=config['ENOCEAN_PORT'])
    # Only listen: never answer other devices' teach-in requests over the air
    communicator.teach_in = False
    communicator.stats.enable_sender_tracking()
    communicator.start()
    yield communicator
    communicator.stop()
    communicator.join(2)


@pytest.fixture
def radio(communicator: SerialCommunicator, config: dict[str, str]) -> Radio:
    radio = Radio(communicator, float(config.get('ENOCEAN_TEST_TIMEOUT', 30)))
    radio.drain()
    return radio


@pytest.fixture
def say(capsys: pytest.CaptureFixture[str]) -> Callable[[str], None]:
    """Prints to the terminal even though pytest captures output."""

    def say(message: str) -> None:
        with capsys.disabled():
            print('\n>>> %s' % message, flush=True)

    return say
