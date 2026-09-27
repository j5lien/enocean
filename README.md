# Python EnOcean

[![CI](https://github.com/j5lien/enocean/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/j5lien/enocean/actions/workflows/ci.yml)

A Python library for reading and controlling [EnOcean](https://www.enocean.com/) radio devices (switches, sensors,
actuators…) through an EnOcean USB/serial module (e.g. USB 300) or a TCP bridge.

It implements the EnOcean Serial Protocol 3 (ESP3) and decodes/encodes telegrams according to the EnOcean Equipment
Profiles (EEP) defined in [`enocean/protocol/EEP.xml`](enocean/protocol/EEP.xml). See
[SUPPORTED_PROFILES.md](SUPPORTED_PROFILES.md) for the full list.

This is a maintained fork of [kipe/enocean](https://github.com/kipe/enocean), which is no longer maintained.

## Installation

Requires Python 3.10 or later.

```bash
pip install git+https://github.com/j5lien/enocean.git@1.0.0
# or, in a uv-managed project
uv add git+https://github.com/j5lien/enocean.git --tag 1.0.0
```

Wheels are also attached to each [GitHub release](https://github.com/j5lien/enocean/releases); see
[CHANGELOG.md](CHANGELOG.md) for what changed.

## Usage

Receive telegrams from a serial module and decode them:

```python
import queue

from enocean.communicators import SerialCommunicator
from enocean.protocol.constants import RORG

communicator = SerialCommunicator(port='/dev/ttyUSB0')
communicator.start()
print('Base ID:', communicator.base_id)

try:
    while communicator.is_alive():
        try:
            packet = communicator.receive.get(timeout=1)
        except queue.Empty:
            continue
        if packet.rorg == RORG.BS4:
            # A5-02-05: temperature sensor, 0°C to +40°C
            packet.parse_eep(0x02, 0x05)
            print(packet.sender_hex, packet.parsed['TMP']['value'], '°C')
finally:
    communicator.stop()
```

Instead of polling `communicator.receive`, you can pass `callback=` to the communicator to be called with each
packet. UTE teach-in requests are answered automatically unless `teach_in=False`.

Build and send a telegram:

```python
from enocean.protocol.constants import RORG
from enocean.protocol.packet import RadioPacket

# D2-01-12, command 1: switch output channel 0 on
packet = RadioPacket.create(
    rorg=RORG.VLD,
    rorg_func=0x01,
    rorg_type=0x12,
    command=1,
    destination=[0x01, 0x94, 0xE3, 0xB9],
    sender=communicator.base_id,
    IO=0,
    OV=100,
)
communicator.send(packet)
```

More in [`examples/`](examples/). `TCPCommunicator` receives packets over TCP instead, for instance from
[`examples/serial_to_tcp.py`](examples/serial_to_tcp.py) running on the machine the module is plugged into.

## Development

The development environment uses [uv](https://docs.astral.sh/uv/):

```bash
make install      # create .venv with the package and dev tools
make hooks        # install the pre-commit hooks (ruff, mypy, uv.lock, SUPPORTED_PROFILES.md)
make test         # run the tests (no hardware needed: a pseudo-terminal stands in for the module)
make test-linux   # same, in a Linux Docker container (PY=3.10 to pick the Python version)
make cov          # tests with coverage
make lint         # ruff check + format check
make format       # ruff format
make profiles     # regenerate SUPPORTED_PROFILES.md after editing EEP.xml
```

Most profile work happens in `EEP.xml`: the Python side is a generic bit-field interpreter driven by it.
`enocean/protocol/tests/test_eep_profiles.py` validates every profile; after an intended decoding change, regenerate
its snapshot with `UPDATE_EEP_SNAPSHOT=1 uv run pytest enocean/protocol/tests/test_eep_profiles.py` and review the
diff.

## Credits

Originally written by Kimmo Huoman ([kipe/enocean](https://github.com/kipe/enocean)), started as part of the
[Forget Me Not](http://www.element14.com/community/community/design-challenges/forget-me-not) design challenge at
[element14](http://www.element14.com/). MIT licensed, see [LICENSE](LICENSE).
