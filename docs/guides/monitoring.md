# Monitoring and logs

## Logs

The library logs through the `enocean` logger and is silent until the application configures logging.
`enocean.consolelogger.init_logging()` sends its logs to stderr, or as one JSON object per line:

```python
import logging

from enocean.consolelogger import init_logging

init_logging(level=logging.INFO, json_format=True)
```

Levels: DEBUG for per-packet traffic and expected radio noise, INFO for lifecycle events (started, base ID, teach-in
answered), WARNING for dropped data (corrupted telegram, unknown profile), ERROR for transport failures.

Records carry structured fields, emitted by the JSON format (and available on the `LogRecord` to any handler). Every
record (but a few DEBUG traces) has an `event` field naming its kind, to filter on it:

| `event` | Level | Other fields |
| --- | --- | --- |
| `packet_received`, `packet_sent` | DEBUG | the packet's fields (below) |
| `teach_in` | INFO | the packet's fields, `outcome` (`accepted`, `deleted`, `profile not supported`) |
| `base_id_received` | INFO | `base_id` (`FF:87:CA:00`) |
| `base_id_timeout` | WARNING | |
| `communicator_started`, `communicator_stopped` | INFO | `transport` (`serial`, `tcp`), `port`, `host` (TCP) |
| `client_connected`, `client_disconnected` | DEBUG | `transport`, `host`, `port`, `client` (`192.168.1.10:51234`) |
| `serial_error` | ERROR | `transport`, `port`, `error` |
| `processing_error` | ERROR | the traceback (e.g. of an exception raised by the callback) |
| `header_crc_error` | DEBUG | |
| `data_crc_error` | WARNING | `packet_type`, `length` |
| `malformed_packet` | WARNING | `packet_type`, `data`, `optional` (hex, to replay it) |
| `unknown_profile` | WARNING | `eep` (`D2-01-12`), `command` |
| `unknown_field` | WARNING | `shortcut` |
| `invalid_packet` | ERROR | (`send()` was given something else than a packet) |
| `profiles_not_loaded` | WARNING | (broken installation) |

The packet's fields use the names and formats of `packet.to_dict()`: `packet_type` and `rorg` (enum names, e.g.
`RADIO_ERP1`, `VLD`), and for radio telegrams `sender`, `destination`, `dbm` (None for telegrams to send), `status`,
`repeater_count` and `eep` (once decoded, e.g. with a device registry).

## Statistics and health

Every communicator keeps statistics, with no dependency:

```python
snapshot = communicator.stats.snapshot()
print(snapshot.packets_received, snapshot.parse_errors, snapshot.last_packet_received_at)

health = communicator.health(max_silence=600)  # no packet for 10 minutes counts as a problem
if not health.healthy:
    print(health.problems)
```

`communicator.stats.enable_sender_tracking(max_senders=500)` also keeps per-device statistics (packets, last heard,
signal strength), bounded so that devices picked up from the neighbourhood can't grow memory forever.

## Prometheus

With the optional dependency (`pip install "enocean[prometheus]"`):

```python
from prometheus_client import start_http_server

from enocean.prometheus import register

register(communicator, max_silence=600)  # or {'usb0': com0, 'usb1': com1}; namespace=, const_labels=, registry=
start_http_server(9100)
```

Metrics are read from the communicator when scraped: packets received and sent (by packet type and RORG), bytes, parse
errors, teach-in responses, base ID requests, transport and processing errors, last packet time, `up`, `healthy`,
queue sizes; per device with `per_sender=True`. `examples/prometheus_exporter.py` is a ready-to-run exporter.
