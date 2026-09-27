# Controlling actuators

Actuators only obey senders they have been taught in with (see [Teach-in](teach-in.md)). Commands are sent from the
module's base ID, or another ID of its range with `sender=`.

```python
from enocean import BlindActuator, SerialCommunicator, SwitchActuator

communicator = SerialCommunicator(port='/dev/ttyUSB0')
communicator.start()

light = SwitchActuator(communicator, '05:99:77:AF')  # D2-01-12 by default
light.turn_on(channel=1)
light.set_output(50, channel=0)  # dimmers: 0 to 100 %
light.query_status()  # the actuator answers with a status telegram (command 4)

cover = BlindActuator(communicator, '05:97:BA:73')  # D2-05-00 by default
cover.go_to(position=50)  # 0: fully open / up
cover.stop()
cover.query_position()
```

Replies arrive like any other telegram; with the actuators in the communicator's [device registry](devices.md) they come
decoded (`packet.parsed['OV']`, `packet.parsed['POS']`…).

Channels are 0-based; `ALL_CHANNELS` (the default of `SwitchActuator`) addresses every output.

## Other telegrams

Any telegram can be built from its profile's fields with `RadioPacket.create()` (see `EEP().describe()` for the
fields), then sent with `communicator.send()`:

```python
--8<-- "build_telegram.py"
```
