# Teach-in

With UTE teach-in (most VLD actuators, e.g. NodOn SIN-2-2-01 and SIN-2-RS-01), the device sends a request announcing
its profile, and the controller answers; the device then obeys the module's ID.

```python
from enocean import SerialCommunicator

communicator = SerialCommunicator(port='/dev/ttyUSB0', teach_in=False)  # don't pair with anyone outside learn()
communicator.start()

# Put the actuator in learn mode now (e.g. press its button), within 30 s
devices = communicator.learn(timeout=30, max_devices=1)
print(devices)  # added to communicator.devices, so their telegrams come decoded
```

- With `teach_in=True` (the default), requests are answered at any time, including those of a neighbour's devices put
  in learn mode: prefer `teach_in=False` and `learn()` windows.
- Deletion requests, and repeated requests from devices already known, are answered as deletions (the device forgets
  the module); requests announcing a profile the library doesn't know are refused.
- `UTETeachInPacket` packets are also delivered to the application: `packet.eep_id` is the announced profile.

RPS switches need no teach-in to be received: register their ID and profile in a [device registry](devices.md).
