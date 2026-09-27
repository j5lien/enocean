#!/usr/bin/env python
"""
Serves Prometheus metrics for an EnOcean module: python examples/prometheus_exporter.py --port /dev/ttyUSB0
Requires `pip install "enocean[prometheus]"`. Metrics are at http://localhost:9100/metrics.
"""

import argparse
import logging
import queue

from prometheus_client import start_http_server

from enocean.communicators import SerialCommunicator
from enocean.consolelogger import init_logging
from enocean.prometheus import register


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--port', default='/dev/ttyUSB0', help='serial port of the EnOcean module')
    parser.add_argument('--listen', type=int, default=9100, help='HTTP port serving /metrics')
    parser.add_argument('--max-silence', type=float, default=600, help='seconds without packets before unhealthy')
    parser.add_argument('--per-sender', action='store_true', help='also export per-device metrics')
    parser.add_argument('--json-logs', action='store_true', help='log as JSON lines')
    args = parser.parse_args()

    init_logging(level=logging.INFO, json_format=args.json_logs)
    communicator = SerialCommunicator(port=args.port)
    register(communicator, max_silence=args.max_silence, per_sender=args.per_sender)
    start_http_server(args.listen)
    communicator.start()

    try:
        while communicator.is_alive():
            try:
                # Consume packets so the receive queue doesn't grow; decode or forward them here as needed
                communicator.receive.get(timeout=1)
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        pass
    finally:
        communicator.stop()


if __name__ == '__main__':
    main()
