# Devices and decoding

Telegrams don't say which profile they follow: the receiver must know each device's profile. A `DeviceRegistry`
records them, and communicators given one deliver packets already decoded.

```python
--8<-- "registry.py"
```

## With a communicator

```python
from enocean import RORG, DeviceRegistry, SerialCommunicator

devices = DeviceRegistry.from_config(
    {
        '00:37:7E:06': {'eep': 'F6-02-02', 'name': 'Office wall switch'},
        '05:99:77:AF': {'eep': 'D2-01-12', 'name': 'Office light'},
    },
    defaults={RORG.RPS: 'F6-02-02'},
    ignored=['FF:E8:06:02'],
)
communicator = SerialCommunicator(port='/dev/ttyUSB0', devices=devices)
communicator.start()

packet = communicator.receive.get()
print(packet.device.name if packet.device else 'unknown', packet.eep_id, packet.parsed)
```

- Known devices are decoded with their profile, and the variant of multi-command profiles is recognized from the
  telegram. `packet.device` is the `Device`, `packet.eep_id` the profile applied and `packet.command` the variant.
- Unknown devices are decoded with the default profile of their RORG, if any; `packet.device` is `None`.
- Telegrams from ignored devices are dropped (and counted as `packets_ignored` in the statistics).
- Teach-in requests and non-radio packets are delivered as they are.

## Configuration

`DeviceRegistry.from_config()` takes a mapping, e.g. loaded from JSON, YAML or TOML: `eep` is the profile, `name` a
label, and any other key goes to `device.metadata`. The `{'rorg': ..., 'func': ..., 'type': ...}` form is accepted
instead of `eep`. Devices can also be added at run time: `devices.add(Device('05:99:77:AF', EEPId.parse('D2-01-12')))`.

## Serializing packets

`packet.to_dict()` gives a JSON-serializable view: IDs and bytes as hex strings, enum names that fall back to hex for
unknown values, the ISO 8601 reception time (UTC), the EEP, the decoded values and the device. It is meant for indexing,
publishing (MQTT…) or logging packets.
