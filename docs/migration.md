# Migration

## From kipe/enocean 0.60 to 1.0

- **Python 3.10 or later.** Python 2 compatibility code is gone.
- **Dependencies**: only `pyserial>=3.5`; `beautifulsoup4` and `enum-compat` are no longer needed.
- `EEP.soup` (BeautifulSoup) was replaced by the standard library's `xml.etree`.

## From 1.0 to 2.0

The 2.0 changes are listed in the [changelog](changelog.md); the ones most likely to affect an application follow.

### Imports and construction

```python
# Before
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.constants import PACKET, RORG

communicator = SerialCommunicator()  # defaulted to /dev/ttyAMA0
communicator.start()
communicator.teach_in = False  # raced with teach-ins arriving meanwhile

# After
from enocean import PACKET, RORG, SerialCommunicator

communicator = SerialCommunicator(port='/dev/ttyUSB0', teach_in=False)  # port required
communicator.start()
```

- `PACKET.RADIO` / `PACKET.RADIO_ADVANCED` → `PACKET.RADIO_ERP1` / `PACKET.RADIO_ERP2`.
- `RORG` is no longer importable from `enocean.protocol.eep`.
- `enocean.decorators` is gone; `examples/enocean_example.py` is no longer installed as a script.

### Choosing profiles: use a device registry

```python
# Before: a table of profiles, and select_eep() by hand
KNOWN_DEVICES = {'05:99:77:AF': {'rorg': RORG.VLD, 'func': 0x01, 'type': 0x12}}
if packet.sender_hex in KNOWN_DEVICES:
    profile = KNOWN_DEVICES[packet.sender_hex]
    packet.select_eep(profile['func'], profile['type'])
    packet.parse_eep()

# After: the same table, and packets come decoded
from enocean import DeviceRegistry

devices = DeviceRegistry.from_config(KNOWN_DEVICES)  # the {'rorg', 'func', 'type'} form is accepted
communicator = SerialCommunicator(port='/dev/ttyUSB0', devices=devices)
```

Multi-command profiles (e.g. D2-01-12) were decoded with their first variant unless `command=` was given: a light's
"set output" command was read with the status layout. The command is now recognized from the telegram.

### Serializing packets

```python
# Before: built by hand, reading private attributes; RORG(packet.data[0]) raised on unknown values
doc = {'rorg': RORG(packet.data[0]).name, 'bit_status': str(packet._bit_status)}  # and so on

# After
doc = packet.to_dict()
```

### Field names and values

The profiles are generated from the official specification, with its field names and descriptions:

| Profile | Before | After |
|---|---|---|
| A5-07-01 | `PIR` | `PIRS` |
| A5-09-06 | `ACT` | `Act` |
| A5-09-07 | `PM2.5`, `PM2.5a` | `PM25`, `PM25a` |
| A5-09-0C | `CONC` | `Conc` |
| A5-11-02 | `CTS` | `CST` |
| D2-01-xx | `DE`, `DN`, `EP`, `QU`, `MDLSB`, `MDMSB` | `de`, `dn`, `ep`, `qu`, `MD_LSB`, `MD_MSB` |
| F6-02-04 | `EB`, `RAO`, `RBO` | `EBO`, `RA0`, `RB0` |

- 4BS and 1BS profiles also decode their learn bit (`LRNB`, `LRN`).
- Descriptions changed, e.g. F6-02-02 `R1`: `'Button AI'` → `'Button AI: "Switch light on" or ...'`; D2-01 `IO`:
  `'Output channel 1 (to load)'` → `'Output channel (to load): 1'`. Compare `raw_value` rather than descriptions where
  possible. `create()` still accepts the short label: `R1='Button AI'`.
- Some enum ranges decode to numbers, e.g. D2-05 `POS` is `50.0` (%) rather than `'Output position 50%'`.
- A released rocker switch (NU bit cleared) decodes with the specification's variant: `R1` is `'no button'`.
- Decoding follows the specification where the old definitions differed: A5-04-02 temperature scale, A5-20-01 direction
  2 `TMP`, A5-38-08 `EDIM` (a percentage), A5-13-01 (weather station telegrams with identifier 1 only; the others are
  A5-13-02 to A5-13-06).

### Other changes

- `packet.received` is a timezone-aware UTC datetime, set when parsing (it was naive local time, set by the
  communicator); comparing it with naive datetimes raises `TypeError`.
- `RadioPacket.dBm` → `RadioPacket.dbm`, `None` when the module didn't report it (`dBm` still works, with a
  `DeprecationWarning`). `UTETeachInPacket.channel` → `number_of_channels` (idem).
- `Packet(type, data)` accepts `bytes`/`bytearray` data and raises `TypeError` for other types (they were silently
  replaced by an empty list).
- `EEP.xml` is replaced by `enocean/protocol/profiles/` (one file per profile, loaded on first use); `EEP.xml_root` by
  `EEP.xml_index`.
- UTE teach-in: deletion requests are answered as deletions (they were accepted as teach-ins).
