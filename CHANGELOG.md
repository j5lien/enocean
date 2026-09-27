# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

Towards 2.0.0: fixes and removal of deprecated APIs, before reworking the public API.

### Breaking changes

- `SerialCommunicator` requires its `port` (the default was `/dev/ttyAMA0`, a Raspberry Pi UART).
- `packet.received` is a timezone-aware UTC datetime, set by `Packet.parse_msg()` (was a naive local datetime set by
  the communicator); comparing it with naive datetimes raises `TypeError`.
- `Packet(...)` raises `TypeError` for data or optional data that isn't a list of ints, `bytes`, `bytearray` or a
  tuple (it was silently replaced by an empty list).
- Removed `PACKET.RADIO` and `PACKET.RADIO_ADVANCED`: use `PACKET.RADIO_ERP1` and `PACKET.RADIO_ERP2`
  (`PACKET(1).name` is now `RADIO_ERP1`).
- Removed `enocean.decorators` (a test helper).
- `examples/enocean_example.py` is no longer installed as a script.
- `enocean.protocol.eep` no longer re-exports `RORG`: import it from `enocean.protocol.constants`.

### Deprecated

- `UTETeachInPacket.channel`: use `number_of_channels`.
- `RadioPacket.dBm`: use `dbm`, which is `None` instead of 0 when the module didn't report the signal strength.

### Added

- `packet.to_dict()`: JSON-serializable view of a packet (hex IDs, enum names that don't raise on unknown values,
  ISO reception time, EEP and decoded values).
- `EEPId` (`EEPId.parse('D2-01-12')`), `packet.eep_id` and `packet.command`: the profile and command variant applied.
- `DeviceRegistry` / `Device` (`enocean.devices`): known devices and their profiles, default profiles per RORG and
  ignored devices. Communicators given `devices=` deliver packets decoded with their device's profile (`packet.device`,
  `packet.parsed`) and drop ignored devices (`packets_ignored` statistic and metric).
- Profile introspection: `EEP().profiles()` lists the profiles, `EEP().describe('D2-01-12')` their variants and
  fields (kind, position, unit, ranges, enum values).
- The public API is importable from the package: `from enocean import SerialCommunicator, RadioPacket, RORG`;
  `enocean.__version__`.
- `SerialCommunicator(teach_in=...)`, like `TCPCommunicator`.
- `Packet(...)` accepts `bytes` and `bytearray` data.

### Fixed

- Profiles with several commands (e.g. D2-01-12, D2-05-00): decoding without `command=` picks the variant the
  telegram carries instead of the profile's first one (e.g. a D2-01-12 "set output" command was decoded with the
  status layout).
- `create(command=...)` wrote the command into a field named `CMD` only: A5-13-01 and A5-38-08 packets were sent with
  command 0.
- A5-04-02 temperature scale: raw range 0...250 per the EEP specification (was 0...255, reading up to 1.6 °C low).
- `UTETeachInPacket.number_of_channels` was never read from the telegram (always 0xFF).
- `Packet(type, bytearray(...))` silently lost its data.

## [1.0.0] - 2026-09-27

First release of the [j5lien/enocean](https://github.com/j5lien/enocean) fork of
[kipe/enocean](https://github.com/kipe/enocean), whose last release was 0.60.1.

### Breaking changes

- Python 3.10 or later is required; Python 2 compatibility code is gone.
- `EEP.xml` is loaded with the standard library's `xml.etree` instead of BeautifulSoup: `EEP.soup` is replaced by
  `EEP.xml_root`, and `EEP.telegrams` holds `xml.etree.ElementTree.Element` objects.
- The `beautifulsoup4` and `enum-compat` dependencies are dropped; `pyserial>=3.5` is the only dependency.
- `RadioPacket.create()` raises `ValueError` for an unknown VLD profile (was `AttributeError`).

### Added

- EEP profiles: A5-04-02, A5-09-06, A5-09-07, A5-09-0C, A5-12-00, A5-13-01, D2-01-12, D2-14-30, D2-14-41,
  F6-02-03, F6-02-04.
- `TCPCommunicator` accepts `callback` and `teach_in`, like `SerialCommunicator`.
- Type annotations for the whole package (`py.typed`); decoded fields are typed as `FieldValue`.

### Fixed

- ESP3 parser: a corrupted header or a stray `0x55` no longer makes the parser drop the valid packets that follow; it
  now resynchronizes on the next sync byte after any CRC error.
- Radio packets without optional data (allowed by ESP3, omitted by some gateways) no longer crash the parser.
- Packets too short for their type are returned unparsed instead of raising or being reported as CRC errors.
- Decoding a telegram shorter than its EEP profile no longer raises.
- UTE teach-in received before the base ID is known: the base ID is now requested and the teach-in answered, instead of
  blocking the communicator thread, raising `TypeError` and losing the packet.
- `Communicator.base_id` works with a callback, and no longer reorders the receive queue while fetching the base ID.
- `TCPCommunicator` crashed on every client connection, and only parsed data once the client disconnected.
- `communicators.utils.send_to_tcp_socket` was broken on Python 3.
- `SerialCommunicator` logs write errors before stopping.
- EEP definitions: D2-01-12 enum values written in binary (default state, external button mode), out-of-range dim
  timers and measurement delta ranges; missing telegram length on D2-14-30 and D2-14-41 (`create()` failed); an
  attribute on A5-13-01 that only worked with a case-insensitive parser.
- `SUPPORTED_PROFILES.md` lists every profile again.

### Changed

- Loading `EEP.xml` is about 20× faster and packet creation/decoding about 5× faster.
- Development: uv, pytest (with end-to-end communicator tests on a pseudo-terminal, property-based parser tests and
  tests over every EEP profile), ruff, mypy, pre-commit hooks, GitHub Actions CI and Dependabot.

## [0.60.1] - 2021-06-18

Last release of [kipe/enocean](https://github.com/kipe/enocean).

[Unreleased]: https://github.com/j5lien/enocean/compare/1.0.0...HEAD
[1.0.0]: https://github.com/j5lien/enocean/compare/0.60.1...1.0.0
[0.60.1]: https://github.com/j5lien/enocean/releases/tag/0.60.1
