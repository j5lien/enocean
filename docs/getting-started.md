# Getting started

## Installation

```bash
pip install git+https://github.com/j5lien/enocean.git@2.0.2
# or, in a uv-managed project
uv add git+https://github.com/j5lien/enocean.git --tag 2.0.2
# with Prometheus metrics
pip install "enocean[prometheus] @ git+https://github.com/j5lien/enocean.git@2.0.2"
```

## Finding the module's serial port

| System | Port |
|---|---|
| Linux | `/dev/serial/by-id/usb-EnOcean_GmbH_EnOcean_USB_300_...` (stable across reboots), or `/dev/ttyUSB0` |
| macOS | `/dev/cu.usbserial-...` (use the `cu.` device, not `tty.`) |
| Docker (Linux host) | pass the device: `devices: ["/dev/serial/by-id/usb-EnOcean...:/dev/serial/by-id/usb-EnOcean..."]` |

## Receiving telegrams

```python
import queue

from enocean import RORG, SerialCommunicator

communicator = SerialCommunicator(port='/dev/ttyUSB0')
communicator.start()  # a thread reading the port
print('Base ID:', communicator.base_id)

try:
    while communicator.is_alive():
        try:
            packet = communicator.receive.get(timeout=1)
        except queue.Empty:
            continue
        if packet.rorg == RORG.BS4:
            packet.parse_eep(0x02, 0x05)  # A5-02-05: temperature sensor, 0 °C to +40 °C
            print(packet.sender_hex, packet.parsed['TMP']['value'], '°C')
finally:
    communicator.stop()
```

Instead of polling `communicator.receive`, pass `callback=` to be called with each packet (from the communicator
thread). Rather than choosing the profile yourself, declare your devices: see
[Devices and decoding](guides/devices.md).

## Decoding and building telegrams without a module

Packets can be parsed from bytes and built from profile fields directly:

```python
--8<-- "decode_frame.py"
```

```python
--8<-- "build_telegram.py"
```

`communicator.send(packet)` writes a packet to the module; for lights and blinds, see
[Controlling actuators](guides/actuators.md).
