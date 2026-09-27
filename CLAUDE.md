# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python library implementing the EnOcean serial protocol (ESP3) for reading and controlling EnOcean
radio devices (switches, sensors, etc.) over serial or TCP. Device behavior/data layout is driven by
EnOcean Equipment Profiles (EEP), defined in `enocean/protocol/profiles/` (one XML file per profile, plus `index.xml`) and
parsed with the stdlib `xml.etree.ElementTree`.

## Commands

Dev environment is managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`,
`.python-version`). A `Makefile` wraps the common tasks:
```bash
make install       # uv sync: creates .venv with the package (editable) + dev deps
make hooks         # install pre-commit hooks (ruff, mypy, uv.lock, SUPPORTED_PROFILES.md)
make test          # uv run pytest
make test-linux    # same, in a Linux Docker container (PY=3.10 to pick the version)
make test-hardware # against a real stick configured in .env (copy .env.example); interactive ones ask to press a switch
make cov           # pytest with coverage
make lint          # ruff check + ruff format --check + mypy --strict on the package (config in pyproject.toml)
make format        # ruff format
```

Run a single test file / test:
```bash
uv run pytest enocean/protocol/tests/test_packet.py
uv run pytest enocean/protocol/tests/test_packet.py::test_packet_examples
```

Tests are plain pytest functions (no classes); use `pytest.raises` for expected exceptions.

Hardware tests (`hardware_tests/`, markers `hardware` and `interactive`) run against a real stick and real devices
configured in `.env` (git-ignored; `.env.example` documents the keys, environment variables override it). They are
deselected by default (`addopts`), skipped when the stick isn't configured or plugged in, never run in CI (and can't
run in Docker on macOS: no USB passthrough), and only listen (teach-in auto-answers off, nothing sent over the air).
Helpers live in `hardware_tests/stick.py`, not `conftest.py`, because another test directory has a `conftest` module.
`enocean/protocol/tests/test_real_frames.py` holds telegrams captured from real devices, checked against what the
devices did: add captures there when validating a profile.

Communicator end-to-end tests (`enocean/communicators/tests/test_{serial,tcp}_communicator.py`) run the real
communicator threads with no hardware: a pseudo-terminal stands in for the EnOcean serial module (tests act as
the radio on the pty master side), and TCP tests use real local sockets. Fixtures and sample ESP3 frames live in
`enocean/communicators/tests/conftest.py`; the `running` fixture guarantees threads are stopped and joined.
Serial e2e tests are skipped on Windows (no pty). An unhandled exception in a communicator thread fails the test
(`filterwarnings` in `pyproject.toml`).
Lint rules (ruff: E/W/F/C90/I/UP/B/SIM, line length 120, max complexity 15) and formatting (`ruff format`, single
quotes) are configured in `pyproject.toml`. Multi-line ESP3 frame literals are wrapped in `# fmt: off` / `# fmt: on`
to keep their sync/header/CRC/data/optional layout; do the same for new ones.

The package is fully typed (`py.typed`, `mypy --strict`; tests are not type-checked). `ElementTree.Element`
lookups return `Optional`: use the `_attr`/`_child` helpers in `eep.py`. Decoded fields are `FieldValue` TypedDicts.

`enocean/protocol/profiles/` is **generated, never edited by hand**: `make eep` downloads the official EnOcean Alliance
specification (EEP 2.6.8 XML, not versioned, SHA-256 checked, cached in `.cache/`), converts it with
`tools/generate_eep.py`, and merges `tools/eep_additions.xml` (profiles missing from or unusable in the spec, each with
its reason). CI regenerates them and fails if anything differs. To fix or add a profile, change the generator or the additions,
then:
```bash
make eep           # regenerate enocean/protocol/profiles/ and SUPPORTED_PROFILES.md
UPDATE_EEP_SNAPSHOT=1 uv run pytest enocean/protocol/tests/test_eep_profiles.py   # if decoding changed on purpose
```
The generator's warnings list what the spec expresses but the format can't (split MSB/LSB or signed values, decoded
raw; masked enum values; variants with identical conditions). Shortcuts are the official ones made into identifiers
(`I/O` -> `IO`).
`test_eep_profiles.py` validates every profile (fields fit and don't overlap, enum values fit their
bits, VLD `<data>` declares `bits`), round-trips every enum/value through `RadioPacket.create()`, and compares the
decoding of fixed bit patterns against `eep_snapshot.json`: review the snapshot diff when regenerating it.

There's no build step; it's a pure-Python package (`uv build` produces sdist/wheel).

## Devices

`enocean/devices.py`: `DeviceRegistry` maps device IDs to `Device(id, eep: EEPId, name, metadata)`, with default
profiles per RORG and ignored IDs; `from_config()` also accepts the legacy `{'rorg', 'func', 'type'}` form.
Communicators given `devices=` decode each received radio telegram with `registry.decode()` (sets `packet.device`,
fills `packet.parsed`) and drop ignored devices (counted as `packets_ignored`). `packet.to_dict()` is the
JSON-friendly view; `EEP().describe()` / `profiles()` are the introspection API.

## Monitoring

Every communicator keeps `CommunicatorStats` (`enocean/stats.py`) in `communicator.stats`: thread-safe counters
updated by the communicator thread (packets/bytes received and sent, parse errors by kind, teach-in responses, base ID
requests/timeouts/latency, transport and processing errors, last packet time), read through `stats.snapshot()`.
`Packet.parse_msg(buf, on_error=...)` reports parse error kinds without coupling the protocol layer to stats.
Transports must push received bytes through `Communicator._feed()` so they are counted.
`communicator.health(max_silence=None)` returns a `Health` (running, transport ready, base ID known, queue sizes,
seconds since last packet, `problems`/`healthy`); transports set `self._transport_ready` while their port/socket is
usable.
`enocean/prometheus.py` (optional extra `enocean[prometheus]`) is a custom `prometheus_client` collector reading
stats/health at scrape time; several communicators go in one collector (`communicator` label), since separate
collectors would register duplicate metric names. Keep `prometheus_client` imports confined to that module. Per-sender statistics are opt-in and bounded
(`stats.enable_sender_tracking(max_senders)`, least recently heard evicted) because of label cardinality.

## Logging conventions

The `enocean` logger has a `NullHandler`: the library is silent unless the application configures logging
(`enocean.consolelogger.init_logging()`, optionally `json_format=True`). Levels: DEBUG for per-packet traffic and
expected radio noise (header CRC errors while resynchronizing), INFO for lifecycle events (started/stopped, base ID,
teach-in answered), WARNING for dropped or unusable data (data CRC error, malformed packet, unknown profile), ERROR
for transport failures, `logger.exception` for errors raised while processing packets (e.g. in user callbacks). Pass
lazy `%s` args, never pre-formatted strings, and `extra=packet_log_fields(packet)` on packet-related records so
structured handlers get `packet_type`/`rorg`/`sender`/`dbm`.

## Releasing

Not published to PyPI. Update `CHANGELOG.md` (new `## [x.y.z] - date` section) and `version` in `pyproject.toml`,
merge, then tag `main` with the bare version (`x.y.z`, no `v` prefix, matching the existing tags) and push the tag:
`.github/workflows/release.yml` checks it matches `pyproject.toml`, runs the tests, builds, and creates the GitHub
release with the wheel/sdist and that CHANGELOG section as notes.

## Architecture

### Packet layer (`enocean/protocol/packet.py`)
`Packet` is the base class for every ESP3 message and does double duty as both parser and builder:
- `Packet.parse_msg(buf)` is a static method that consumes a raw byte buffer, validates the two CRC8
  checksums (header and data, via `enocean/protocol/crc8.py`), and returns
  `(PARSE_RESULT, remaining_buffer, packet_or_None)`. Based on `packet_type` and (for radio packets)
  `rorg`, it dispatches to a subclass: `RadioPacket`, `UTETeachInPacket` (RORG.UTE teach-in),
  `ResponsePacket`, or `EventPacket`.
- `Packet.create(...)` is the inverse: given `rorg`/`rorg_func`/`rorg_type` and EEP field values as
  kwargs, it builds a ready-to-send `Packet` (only `RADIO_ERP1` with RORG `RPS`/`BS1`/`BS4`/`VLD` is
  supported). `RadioPacket.create(...)` is the convenience entry point most callers use.
- Packet data is manipulated as a **bit array**, not bytes: `_bit_data` (a property) converts
  `self.data` to/from a list of booleans, since EEP fields are bit-packed and don't align to byte
  boundaries. `select_eep()` picks the EEP profile (needed to know the bit width, e.g. for VLD
  packets), `parse_eep()` decodes fields into `self.parsed`, and `set_eep()` writes fields back into
  the bit array.
- Constants for indexing into data bytes from the end of the array (`DB0`, `DB2`, `DB3`, `DB4`, `DB6`
  in `enocean/protocol/constants.py`) are used because message length varies but the trailing fields
  (sender, status) are fixed-offset-from-the-end.

### EEP layer (`enocean/protocol/eep.py`)
`EEP` reads `profiles/index.xml` on construction (`EEP.xml_index`) and exposes `self.telegrams[rorg][func][type]`, a
lazy mapping: each profile file is parsed on first access and cached (`Packet.eep` is the shared instance), so only
the profiles an application uses are loaded. Values are `ElementTree.Element`s. Elements without children are falsy, so compare
lookups with `is None`, never `if not element`. `find_profile()` looks up a profile by RORG/FUNC/TYPE (and optional
`direction`/`command`), otherwise picks the `<data>` variant whose `<condition source="data|status" offset size
value>` elements the telegram matches (most specific first), falling back to the first variant. `create()` writes the
selected variant's conditions (except fields given explicitly) so a built telegram decodes as that variant.
`get_values()`/`set_values()` walk a profile's `<value>`, `<enum>`, and `<status>` child tags to
decode/encode bit-packed fields — `<value>` does linear range→scale interpolation, `<enum>` maps raw
integers to descriptions (including `<rangeitem>` ranges, which may carry `scale-min`/`scale-max`/`unit` and then
decode to a number), `<status>` are single-bit booleans read from `Packet.status`, not `Packet.data`.

The Python side is a generic bit-field interpreter driven entirely by the XML; profile changes go through the
generator or `tools/eep_additions.xml`.

### Communicator layer (`enocean/communicators/`)
`Communicator` (base class, in `communicator.py`) is a `threading.Thread` that owns a `transmit` and
`receive` `queue.Queue`, an internal byte buffer, and a `parse()` loop that repeatedly calls
`Packet.parse_msg()` until the buffer is exhausted, dispatching complete packets either to a
user-supplied `callback` or to the `receive` queue. It also auto-answers `UTETeachInPacket` teach-in
requests unless `teach_in=False`. `base_id` is lazily fetched from the module via a
`COMMON_COMMAND`/`CO_RD_IDBASE` request/response round-trip (blocks briefly, draining `receive` and
putting back anything that isn't the response it's waiting for).

`SerialCommunicator` and `TCPCommunicator` subclass `Communicator` and implement `run()` — each just
pumps bytes in and out of a `pyserial` serial port or a TCP socket respectively, and calls
`self.parse()`. Prefer adding new transports as `Communicator` subclasses rather than changing the
base class's queue/threading contract.

### Typical usage flow (see `examples/`)
1. Instantiate a communicator (`SerialCommunicator(port=...)`), `.start()` it (runs as a thread).
2. Build outgoing packets with `RadioPacket.create(rorg=..., rorg_func=..., rorg_type=..., **eep_fields)`
   and `communicator.send(packet)`.
3. Pull incoming packets from `communicator.receive` (or via callback), then call
   `packet.select_eep(func, type)` + `packet.parse_eep()` (or the combined `packet.parse_eep(func, type)`)
   to decode fields into `packet.parsed`.

## Compatibility notes

- Python >= 3.10 only (`requires-python`); CI (`.github/workflows/ci.yml`) tests 3.10–3.14 on Linux, plus 3.14 on
  macOS/Windows, and checks `uv.lock` is current, ruff, `SUPPORTED_PROFILES.md` freshness, coverage >= 90%, and that
  the built wheel imports and loads its profiles. Actions are pinned by commit SHA; Dependabot
  (`.github/dependabot.yml`) bumps them and the uv dependencies weekly.
- The Python 2 compatibility code has been removed; don't reintroduce `from __future__` imports, `Queue` fallbacks
  or `super(Class, self)`.
