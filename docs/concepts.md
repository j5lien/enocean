# Concepts

## ESP3 packets

The module talks to the computer with the **EnOcean Serial Protocol 3** (ESP3): a stream of packets, each starting
with the sync byte `0x55`, a header (data length, optional data length, packet type) protected by a CRC8, then the data
and optional data protected by a second CRC8. `Packet.parse_msg()` reads them from the byte stream; on a CRC error it
skips the sync byte and resynchronizes on the next packet, so radio noise never costs the valid packets that follow.

The packet type (`PACKET`) tells what a packet is:

| Type | Class | Content |
|---|---|---|
| `RADIO_ERP1` | `RadioPacket`, `UTETeachInPacket` | a radio telegram received from, or to send to, a device |
| `RESPONSE` | `ResponsePacket` | the module's answer to a command (`RETURN_CODE`) |
| `EVENT` | `EventPacket` | an event reported by the module |
| `COMMON_COMMAND` | `Packet` | a command to the module, e.g. read its base ID or version |

A radio telegram's optional data carries the destination ID and the signal strength (`packet.dbm`).

## Telegram types and profiles (EEP)

The first byte of a radio telegram is its **RORG**, the telegram type:

| RORG | Name | Payload |
|---|---|---|
| `F6` | RPS | 1 byte, e.g. energy-harvesting rocker switches |
| `D5` | 1BS | 1 byte, e.g. contacts |
| `A5` | 4BS | 4 bytes, e.g. sensors |
| `D2` | VLD | variable length, e.g. actuators |
| `D4` | UTE | teach-in requests |

The meaning of the payload bits is defined by the device's **EnOcean Equipment Profile** (EEP), identified as
`RORG-FUNC-TYPE`: `D2-01-12` is a VLD telegram, function 01 (electronic switches and dimmers), type 12. The receiver
must know each device's profile: telegrams don't carry it (only teach-in telegrams announce it). That's what the
[device registry](guides/devices.md) is for.

A profile may have several **variants**: per **direction** (to or from the device), per **command** (e.g. D2-01-12
command 1 "set output" and command 4 "status response" have different layouts), or selected by other bits of the
telegram (e.g. F6-02-02 by the status bits T21/NU). When decoding, the library recognizes the variant from the
telegram; when building one, `command=` selects it.

Decoded fields are keyed by their **shortcut** (e.g. `OV` for output value), each giving `value` (a number, a
description or a boolean), `raw_value`, `unit` and `description` (a `FieldValue`). `EEP().describe('D2-01-12')` lists
the fields of each variant; [SUPPORTED_PROFILES.md](https://github.com/j5lien/enocean/blob/main/SUPPORTED_PROFILES.md)
lists them all.

## IDs and the base ID

Every EnOcean device has a unique 4-byte **ID** (`05:99:77:AF`), sent as the sender of its telegrams. The module can
send from its own chip ID or, more commonly, from its **base ID** range: 128 consecutive IDs starting at the base ID
(e.g. `FF:C3:6F:80` to `FF:C3:6F:FF`), so one module can act as several senders. `communicator.base_id` asks the
module for it.

## Teach-in

Devices only act on telegrams from senders they have been **taught in** with, and a receiver must know which devices
to listen to and with which profile. Depending on the telegram type:

- **RPS** (switches): any telegram can teach the switch in to an actuator put in learn mode.
- **1BS / 4BS**: a learn bit tells teach-in telegrams from data telegrams; 4BS teach-in telegrams may carry the
  profile.
- **UTE** (Universal Teach-in, mostly VLD devices): the device sends a teach-in request announcing its profile and the
  controller answers; both learn each other's ID. See [Teach-in](guides/teach-in.md).
