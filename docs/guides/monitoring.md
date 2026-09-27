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
answered), WARNING for dropped data (corrupted telegram, unknown profile), ERROR for transport failures. Packet-related
records carry `packet_type`, `rorg`, `sender` and `dbm` fields.

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
