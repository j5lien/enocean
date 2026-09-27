"""Commands for actuators, sent through a communicator whose module is taught in to them.

    light = SwitchActuator(communicator, '05:99:77:AF')     # D2-01 switch/dimmer
    light.turn_on(channel=1)
    light.query_status()                                    # the actuator answers with a status telegram (command 4)

    cover = BlindActuator(communicator, '05:97:BA:73')      # D2-05 blinds/shutters
    cover.go_to(position=50)
    cover.stop()

The sender is the module's base ID unless another ID of its range is given. Replies arrive like any other telegram
(decoded automatically when the actuators are in the communicator's DeviceRegistry).
"""

from collections.abc import Iterable
from typing import Any

from enocean.communicators.communicator import Communicator
from enocean.devices import device_id
from enocean.protocol.eep import EEPId
from enocean.protocol.packet import RadioPacket
from enocean.utils import from_hex_string

# D2-01 I/O channel value addressing every output channel
ALL_CHANNELS = 0x1E
# D2-05 position/angle value leaving the current one unchanged
UNCHANGED = 127


class Actuator:
    """Base class: sends VLD commands of the actuator's profile to it."""

    def __init__(
        self,
        communicator: Communicator,
        id: str | Iterable[int],
        eep: EEPId | str,
        sender: list[int] | None = None,
    ) -> None:
        """Bind an actuator to the communicator that reaches it.

        Args:
            communicator: The communicator (started) whose module is taught in to the actuator.
            id: The actuator's ID, '05:99:77:AF' or bytes.
            eep: Its profile.
            sender: The ID to send from: one of the module's range (base ID to base ID + 127) the actuator was taught
                in with. Defaults to the module's base ID.
        """
        self.communicator = communicator
        self.id = device_id(id)
        self.eep = EEPId.parse(eep)
        self.sender = sender

    @property
    def destination(self) -> list[int]:
        """The actuator's ID as bytes."""
        destination = from_hex_string(self.id)
        assert isinstance(destination, list)
        return destination

    def send_command(self, command: int, **fields: Any) -> RadioPacket:
        """Build and send a command of the actuator's profile.

        Args:
            command: The command number (e.g. 1 for D2-01 Actuator Set Output).
            **fields: The command's field values, e.g. IO=0, OV=100 (see EEP().describe()).

        Returns:
            The packet sent.

        Raises:
            RuntimeError: The module's base ID is unknown and no sender was given.
        """
        sender = self.sender or self.communicator.base_id
        if sender is None:
            raise RuntimeError('The base ID of the module is unknown: give a sender or check the module responds')
        packet = RadioPacket.create(
            rorg=self.eep.rorg,
            rorg_func=self.eep.func,
            rorg_type=self.eep.type,
            command=command,
            destination=self.destination,
            sender=list(sender),
            **fields,
        )
        self.communicator.send(packet)
        return packet


class SwitchActuator(Actuator):
    """D2-01 electronic switches and dimmers (e.g. NodOn SIN-2-2-01: D2-01-12). Channels are 0-based."""

    def __init__(
        self,
        communicator: Communicator,
        id: str | Iterable[int],
        eep: EEPId | str = 'D2-01-12',
        sender: list[int] | None = None,
    ) -> None:
        super().__init__(communicator, id, eep, sender)

    def set_output(self, value: int, channel: int = ALL_CHANNELS) -> RadioPacket:
        """Command 1, Actuator Set Output.

        Args:
            value: 0 (off) to 100 (on, or 100 % for dimmers).
            channel: The output channel (0-based), or ALL_CHANNELS.

        Returns:
            The packet sent.

        Raises:
            ValueError: value is out of 0..100.
        """
        if not 0 <= value <= 100:
            raise ValueError('Output value must be between 0 and 100, got %r' % value)
        return self.send_command(1, DV=0, IO=channel, OV=value)

    def turn_on(self, channel: int = ALL_CHANNELS) -> RadioPacket:
        """Switch a channel (or all) on: set_output(100)."""
        return self.set_output(100, channel)

    def turn_off(self, channel: int = ALL_CHANNELS) -> RadioPacket:
        """Switch a channel (or all) off: set_output(0)."""
        return self.set_output(0, channel)

    def query_status(self, channel: int = ALL_CHANNELS) -> RadioPacket:
        """Command 3, Actuator Status Query: the actuator answers with Actuator Status Response (command 4)."""
        return self.send_command(3, IO=channel)


class BlindActuator(Actuator):
    """D2-05 blinds control (e.g. NodOn SIN-2-RS-01: D2-05-00). Positions and angles in % (0: open/up)."""

    def __init__(
        self,
        communicator: Communicator,
        id: str | Iterable[int],
        eep: EEPId | str = 'D2-05-00',
        sender: list[int] | None = None,
    ) -> None:
        super().__init__(communicator, id, eep, sender)

    def go_to(self, position: int | None = None, angle: int | None = None, channel: int = 0) -> RadioPacket:
        """Command 1, Go to Position and Angle.

        Args:
            position: Vertical position in % (0: fully open/up), None to leave it unchanged.
            angle: Slat rotation angle in %, None to leave it unchanged.
            channel: The channel.

        Returns:
            The packet sent.

        Raises:
            ValueError: position or angle is out of 0..100.
        """
        for name, value in (('position', position), ('angle', angle)):
            if value is not None and not 0 <= value <= 100:
                raise ValueError('%s must be between 0 and 100, got %r' % (name.capitalize(), value))
        return self.send_command(
            1,
            POS=UNCHANGED if position is None else position,
            ANG=UNCHANGED if angle is None else angle,
            REPO=0,
            LOCK=0,
            CHN=channel,
        )

    def stop(self, channel: int = 0) -> RadioPacket:
        """Command 2, Stop."""
        return self.send_command(2, CHN=channel)

    def query_position(self, channel: int = 0) -> RadioPacket:
        """Command 3, Query Position and Angle: the actuator answers with Reply Position and Angle (command 4)."""
        return self.send_command(3, CHN=channel)
