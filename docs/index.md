# Python EnOcean

A Python library for reading and controlling [EnOcean](https://www.enocean.com/) radio devices (switches, sensors,
actuators…) through an EnOcean USB/serial module (e.g. USB 300) or a TCP bridge.

- **ESP3**: parses the EnOcean Serial Protocol 3 byte stream, resynchronizing after radio noise or corrupted bytes, and
  builds packets to send.
- **270 profiles**: decodes and encodes telegrams according to the EnOcean Equipment Profiles (EEP) of the official
  EnOcean Alliance specification.
- **Integration**: a device registry decoding received telegrams automatically, JSON-serializable packets, commands for
  lights and blinds, teach-in.
- **Operation**: statistics, health checks, Prometheus metrics, structured logs.

It requires Python 3.10 or later, and has one dependency: `pyserial`.

```bash
pip install git+https://github.com/j5lien/enocean.git@2.0.1
```

```python
--8<-- "decode_frame.py"
```

Next: [Getting started](getting-started.md), then the [concepts](concepts.md) behind EnOcean.

This is a maintained fork of [kipe/enocean](https://github.com/kipe/enocean).
