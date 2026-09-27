"""
Known devices and the profile (EEP) each one speaks, so received telegrams can be decoded automatically.

    registry = DeviceRegistry.from_config(
        {
            '00:37:7E:06': {'eep': 'F6-02-02', 'name': 'Office wall switch', 'room': 'office'},
            '05:99:77:AF': {'eep': 'D2-01-12', 'name': 'Office light'},
        },
        defaults={RORG.RPS: 'F6-02-02'},
        ignored=['FF:E8:06:02'],
    )
    communicator = SerialCommunicator(port, devices=registry)  # received packets come decoded

Or decode packets yourself with registry.decode(packet).
"""

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from enocean.protocol.eep import EEPId
from enocean.protocol.packet import Packet, RadioPacket, UTETeachInPacket
from enocean.utils import to_hex_string


def device_id(value: str | Iterable[int]) -> str:
    """Normalizes a device ID: '05:99:77:af' or [0x05, 0x99, 0x77, 0xAF] -> '05:99:77:AF'."""
    if isinstance(value, str):
        return value.strip().upper()
    return to_hex_string(value)


@dataclass(frozen=True)
class Device:
    """A known device: its ID, the profile it speaks, and free-form information (room, owner...)."""

    id: str
    eep: EEPId
    name: str = ''
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {'id': self.id, 'eep': str(self.eep), 'name': self.name, 'metadata': dict(self.metadata)}


class DeviceRegistry:
    """
    Devices by ID. defaults gives the profile to try for unknown devices, by RORG (e.g. {RORG.RPS: 'F6-02-02'});
    telegrams from ignored devices are dropped by communicators using this registry.
    """

    def __init__(
        self,
        devices: Iterable[Device] = (),
        defaults: Mapping[int, EEPId | str] | None = None,
        ignored: Iterable[str | Iterable[int]] = (),
    ) -> None:
        self._devices: dict[str, Device] = {}
        self.defaults = {int(rorg): EEPId.parse(eep) for rorg, eep in (defaults or {}).items()}
        self._ignored = {device_id(ignored_id) for ignored_id in ignored}
        for device in devices:
            self.add(device)

    @classmethod
    def from_config(
        cls,
        config: Mapping[str, Mapping[str, Any]],
        defaults: Mapping[int, EEPId | str] | None = None,
        ignored: Iterable[str | Iterable[int]] = (),
    ) -> 'DeviceRegistry':
        """
        Builds a registry from {id: {'eep': 'D2-01-12', 'name': ..., other keys go to metadata}}, e.g. loaded from
        JSON, YAML or TOML. {'rorg': ..., 'func': ..., 'type': ...} is accepted instead of 'eep'.
        """
        devices = []
        for raw_id, entry in config.items():
            info = dict(entry)
            if 'eep' in info:
                eep = EEPId.parse(info.pop('eep'))
            else:
                eep = EEPId(int(info.pop('rorg')), int(info.pop('func')), int(info.pop('type')))
            devices.append(Device(device_id(raw_id), eep, str(info.pop('name', '')), info))
        return cls(devices, defaults, ignored)

    def add(self, device: Device) -> None:
        self._devices[device_id(device.id)] = device

    def remove(self, id: str | Iterable[int]) -> None:
        self._devices.pop(device_id(id), None)

    def get(self, id: str | Iterable[int]) -> Device | None:
        return self._devices.get(device_id(id))

    def ignore(self, id: str | Iterable[int]) -> None:
        self._ignored.add(device_id(id))

    def is_ignored(self, id: str | Iterable[int]) -> bool:
        return device_id(id) in self._ignored

    def __contains__(self, id: object) -> bool:
        return isinstance(id, (str, list, tuple)) and device_id(id) in self._devices

    def __iter__(self) -> Iterator[Device]:
        return iter(self._devices.values())

    def __len__(self) -> int:
        return len(self._devices)

    def eep_for(self, packet: RadioPacket) -> EEPId | None:
        """The profile to decode a telegram with: its device's, else the default for its RORG, if any."""
        device = self.get(packet.sender)
        if device is not None:
            return device.eep
        return self.defaults.get(int(packet.rorg))

    def decode(self, packet: Packet) -> Device | None:
        """
        Decodes a radio telegram with its device's profile (or the default one for its RORG), filling packet.parsed,
        and sets packet.device. Returns the device, None if unknown. Teach-in (UTE) and non-radio packets are left
        as they are.
        """
        if not isinstance(packet, RadioPacket) or isinstance(packet, UTETeachInPacket):
            return None
        device = self.get(packet.sender)
        packet.device = device
        eep = self.eep_for(packet)
        if eep is not None and eep.rorg == packet.rorg:
            packet.parse_eep(eep.func, eep.type)
        return device
