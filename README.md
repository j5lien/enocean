# Python EnOcean

[![CI](https://github.com/j5lien/enocean/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/j5lien/enocean/actions/workflows/ci.yml)

A Python library for reading and controlling [EnOcean](https://www.enocean.com/) radio devices (switches, sensors,
actuators…) through an EnOcean USB/serial module (e.g. USB 300) or a TCP bridge.

It implements the EnOcean Serial Protocol 3 (ESP3) and decodes/encodes telegrams according to the EnOcean Equipment
Profiles (EEP): the 270 profiles of the official EnOcean Alliance specification (EEP 2.6.8), from which
[`enocean/protocol/profiles/`](enocean/protocol/profiles/) is generated (each profile is loaded on first use). See [SUPPORTED_PROFILES.md](SUPPORTED_PROFILES.md)
for the full list, or `EEP().describe('D2-01-12')` from code.

**Documentation: <https://j5lien.github.io/enocean/>** (getting started, concepts, guides, API reference, migration).

This is a maintained fork of [kipe/enocean](https://github.com/kipe/enocean), which is no longer maintained.

## Installation

Requires Python 3.10 or later.

```bash
pip install git+https://github.com/j5lien/enocean.git@2.1.0
# or, in a uv-managed project
uv add git+https://github.com/j5lien/enocean.git --tag 2.1.0
```

Wheels are also attached to each [GitHub release](https://github.com/j5lien/enocean/releases); see
[CHANGELOG.md](CHANGELOG.md) for what changed.

## Usage

Receive telegrams from a serial module and decode them:

```python
import queue

from enocean import RORG, SerialCommunicator

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

Declare your devices and received telegrams come decoded with the right profile:

```python
from enocean import RORG, DeviceRegistry, SerialCommunicator

devices = DeviceRegistry.from_config(
    {
        '00:37:7E:06': {'eep': 'F6-02-02', 'name': 'Office wall switch', 'room': 'office'},
        '05:99:77:AF': {'eep': 'D2-01-12', 'name': 'Office light'},
    },
    defaults={RORG.RPS: 'F6-02-02'},  # profile to try for unknown devices, by RORG
    ignored=['FF:E8:06:02'],  # dropped
)
communicator = SerialCommunicator(port='/dev/ttyUSB0', devices=devices)
communicator.start()

packet = communicator.receive.get()
print(packet.device.name if packet.device else 'unknown', packet.eep_id, packet.parsed)
print(packet.to_dict())  # JSON-serializable, e.g. to index or publish it
```

Profiles with several commands (e.g. D2-01-12) are decoded with the command the telegram carries. To see what a
profile contains: `EEP().describe('D2-01-12')`.

Teach the module in to an actuator (UTE): open a learn window, then put the actuator in learn mode (e.g. press its
button); it announces its profile and learns the module's ID:

```python
communicator = SerialCommunicator(port='/dev/ttyUSB0', teach_in=False)  # don't pair with anyone outside learn()
communicator.start()
devices = communicator.learn(timeout=30, max_devices=1)  # added to communicator.devices
```

With `teach_in=True` (the default), teach-in requests are answered at any time. Deletion requests (and repeated
requests from devices already known) are answered as deletions, and unknown profiles are refused.

Control actuators the module is taught in to:

```python
from enocean import BlindActuator, SwitchActuator

light = SwitchActuator(communicator, '05:99:77:AF')  # D2-01-12 by default
light.turn_on(channel=1)
light.query_status()  # answered by a status telegram (command 4)

cover = BlindActuator(communicator, '05:97:BA:73')  # D2-05-00 by default
cover.go_to(position=50)
cover.stop()
```

Or build any telegram from its profile's fields:

```python
from enocean import RORG, RadioPacket

# D2-01-12, command 1: switch output channel 0 on
packet = RadioPacket.create(
    rorg=RORG.VLD,
    rorg_func=0x01,
    rorg_type=0x12,
    command=1,
    destination=[0x05, 0x99, 0x77, 0xAF],
    sender=communicator.base_id,
    IO=0,
    OV=100,
)
communicator.send(packet)
```

More in [`examples/`](examples/). `TCPCommunicator` receives packets over TCP instead, for instance from
[`examples/serial_to_tcp.py`](examples/serial_to_tcp.py) running on the machine the module is plugged into.

## Monitoring

**Logs.** The library is silent until you configure logging. `enocean.consolelogger.init_logging()` sends its logs to
stderr, or as one JSON object per line with `init_logging(json_format=True)`; records carry an `event` field
(`packet_received`, `teach_in`, `serial_error`...) and structured fields such as `sender`, `rorg`, `eep` or `dbm`, named
as in `packet.to_dict()` (see the [monitoring guide](https://j5lien.github.io/enocean/guides/monitoring/#logs)).

**Statistics and health**, always available, no dependency:

```python
snapshot = communicator.stats.snapshot()
print(snapshot.packets_received, snapshot.parse_errors, snapshot.last_packet_received_at)

health = communicator.health(max_silence=600)  # no packet for 10 minutes counts as a problem
if not health.healthy:
    print(health.problems)
```

**Prometheus**, with the optional dependency (`pip install "enocean[prometheus]"`):

```python
from prometheus_client import start_http_server

from enocean.prometheus import register

register(communicator, max_silence=600)  # or {'usb0': com0, 'usb1': com1}; namespace=, const_labels=, registry=
start_http_server(9100)
```

It exports `enocean_packets_received_total` and `enocean_packets_sent_total` (by `packet_type` and `rorg`),
`enocean_received_bytes_total`, `enocean_sent_bytes_total`, `enocean_parse_errors_total` (by `kind`: `header_crc`,
`data_crc`, `malformed`), `enocean_teach_in_responses_total`, `enocean_base_id_requests_total`,
`enocean_base_id_timeouts_total`, `enocean_base_id_fetch_seconds`, `enocean_transport_errors_total`,
`enocean_processing_errors_total`, `enocean_last_packet_received_timestamp_seconds`, `enocean_start_time_seconds`,
`enocean_up`, `enocean_healthy`, `enocean_base_id_known` and `enocean_queue_size` (by `queue`). Values are read from
the communicator when scraped.

Per-device metrics are opt-in, since each device becomes a time series: `register(communicator, per_sender=True,
max_senders=500)` adds `enocean_sender_packets_received_total`, `enocean_sender_last_seen_timestamp_seconds` and
`enocean_sender_dbm` (by `sender` and `rorg`), keeping the most recently heard `max_senders` devices
(`enocean_senders_evicted_total` counts the others). Without Prometheus, `communicator.stats.enable_sender_tracking()`
fills `snapshot.senders`.

[`examples/prometheus_exporter.py`](examples/prometheus_exporter.py) is a ready-to-run exporter for a serial module.

## Development

The development environment uses [uv](https://docs.astral.sh/uv/):

```bash
make install      # create .venv with the package and dev tools
make hooks        # install the pre-commit hooks (ruff, mypy, uv.lock, SUPPORTED_PROFILES.md)
make test         # run the tests (no hardware needed: a pseudo-terminal stands in for the module)
make test-linux   # same, in a Linux Docker container (PY=3.10 to pick the Python version)
make test-hardware  # against a real EnOcean stick configured in .env (see .env.example), local only
make cov          # tests with coverage
make lint         # ruff (including docstrings) + format check + mypy
make docs         # serve the documentation locally
make format       # ruff format
make eep          # regenerate the profiles from the official specification (downloaded) and tools/eep_additions.xml
```

The profiles are generated: changes go through `tools/generate_eep.py` or `tools/eep_additions.xml`, then
`make eep`. The Python side is a generic bit-field interpreter driven by it.
`enocean/protocol/tests/test_eep_profiles.py` validates every profile; after an intended decoding change, regenerate
its snapshot with `UPDATE_EEP_SNAPSHOT=1 uv run pytest enocean/protocol/tests/test_eep_profiles.py` and review the
diff.

## Credits

Originally written by Kimmo Huoman ([kipe/enocean](https://github.com/kipe/enocean)), started as part of the
[Forget Me Not](http://www.element14.com/community/community/design-challenges/forget-me-not) design challenge at
[element14](http://www.element14.com/). MIT licensed, see [LICENSE](LICENSE).
