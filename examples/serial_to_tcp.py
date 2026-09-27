#!/usr/bin/env python
import queue
import sys
import traceback

from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.communicators.utils import send_to_tcp_socket
from enocean.consolelogger import init_logging

init_logging()
# Serial port of the module, e.g. /dev/ttyUSB0 (Linux) or /dev/cu.usbserial-... (macOS)
communicator = SerialCommunicator(port=sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyUSB0')
communicator.start()
while communicator.is_alive():
    try:
        # Loop to empty the queue...
        packet = communicator.receive.get(block=True, timeout=1)
        send_to_tcp_socket('localhost', 9637, packet)
    except queue.Empty:
        continue
    except KeyboardInterrupt:
        break
    except Exception:
        traceback.print_exc(file=sys.stdout)
        break

if communicator.is_alive():
    communicator.stop()
