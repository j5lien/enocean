"""ESP3 packets: parsing them from the serial stream, building them, decoding and encoding their EEP fields."""

import datetime
import logging
import warnings
from collections import OrderedDict
from collections.abc import Callable, Mapping
from enum import IntEnum
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

import enocean.utils
from enocean.protocol import crc8
from enocean.protocol.constants import DB0, DB2, DB3, DB4, DB6, EVENT_CODE, PACKET, PARSE_RESULT, RETURN_CODE, RORG
from enocean.protocol.eep import EEP, EEPId, FieldValue

if TYPE_CHECKING:
    from enocean.devices import Device


def enum_name(enum: type[IntEnum], value: int) -> str:
    """Name of value in enum, or its hex value ('0x62') if unknown, instead of raising like enum(value)."""
    try:
        return enum(value).name
    except ValueError:
        return '0x%02X' % value


# Kinds of errors reported to Packet.parse_msg(on_error=...)
HEADER_CRC_ERROR = 'header_crc'
DATA_CRC_ERROR = 'data_crc'
MALFORMED_PACKET = 'malformed'


class Packet:
    """An ESP3 packet: its type, data and optional data bytes.

    Packet.parse_msg() reads packets from the byte stream, returning the subclass matching their type (RadioPacket,
    UTETeachInPacket, ResponsePacket, EventPacket); Packet.create() / RadioPacket.create() build radio telegrams from
    EEP field values. Once a profile is applied (parse_eep()), `parsed` holds the decoded fields.

    Args:
        packet_type: The ESP3 packet type (PACKET).
        data: The data bytes.
        optional: The optional data bytes.

    Raises:
        TypeError: data or optional isn't a list of ints, bytes, bytearray or tuple.
    """

    eep = EEP()
    logger = logging.getLogger('enocean.protocol.packet')

    def __init__(
        self,
        packet_type: int,
        data: list[int] | bytes | bytearray | None = None,
        optional: list[int] | bytes | bytearray | None = None,
    ) -> None:
        self.packet_type = packet_type
        self.rorg: int = RORG.UNDEFINED
        self.rorg_func: int | None = None
        self.rorg_type: int | None = None
        self.rorg_manufacturer: int | None = None

        # When the packet was parsed from the serial stream (UTC, timezone-aware); None for packets built locally
        self.received: datetime.datetime | None = None
        self.data = self._int_list(data, 'data')
        self.optional = self._int_list(optional, 'optional')

        self.status = 0
        self.parsed: OrderedDict[str, FieldValue] = OrderedDict()
        self.repeater_count = 0
        self._profile: Element | None = None

        self.parse()

    @staticmethod
    def _int_list(value: list[int] | bytes | bytearray | tuple[int, ...] | None, name: str) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, (bytes, bytearray, tuple)):
            return list(value)
        raise TypeError('Packet %s must be a list of ints, bytes or bytearray, not %s' % (name, type(value).__name__))

    def __str__(self) -> str:
        return '0x%02X %s %s %s' % (
            self.packet_type,
            [hex(o) for o in self.data],
            [hex(o) for o in self.optional],
            self.parsed,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Packet):
            return NotImplemented
        return (
            self.packet_type == other.packet_type
            and self.rorg == other.rorg
            and self.data == other.data
            and self.optional == other.optional
        )

    @property
    def _bit_data(self) -> list[bool]:
        # First and last 5 bits are always defined, so the data we're modifying is between them...
        # TODO: This is valid for the packets we're currently manipulating.
        # Needs the redefinition of Packet.data -> Packet.message.
        # Packet.data would then only have the actual, documented data-bytes.
        # Packet.message would contain the whole message.
        # See discussion in issue #14
        return enocean.utils.to_bitarray(self.data[1 : len(self.data) - 5], (len(self.data) - 6) * 8)

    @_bit_data.setter
    def _bit_data(self, value: list[bool]) -> None:
        # The same as getting the data, first and last 5 bits are ommitted, as they are defined...
        for byte in range(len(self.data) - 6):
            self.data[byte + 1] = enocean.utils.from_bitarray(value[byte * 8 : (byte + 1) * 8])

    # # COMMENTED OUT, AS NOTHING TOUCHES _bit_optional FOR NOW.
    # # Thus, this is also untested.
    # @property
    # def _bit_optional(self):
    #     return enocean.utils.to_bitarray(self.optional, 8 * len(self.optional))

    # @_bit_optional.setter
    # def _bit_optional(self, value):
    #     if self.rorg in [RORG.RPS, RORG.BS1]:
    #         self.data[1] = enocean.utils.from_bitarray(value)
    #     if self.rorg == RORG.BS4:
    #         for byte in range(4):
    #             self.data[byte+1] = enocean.utils.from_bitarray(value[byte*8:(byte+1)*8])

    @property
    def _bit_status(self) -> list[bool]:
        return enocean.utils.to_bitarray(self.status)

    @_bit_status.setter
    def _bit_status(self, value: list[bool]) -> None:
        self.status = enocean.utils.from_bitarray(value)

    @staticmethod
    def parse_msg(
        buf: bytes | bytearray | list[int], on_error: Callable[[str], None] | None = None
    ) -> tuple[PARSE_RESULT, list[int], 'Packet | None']:
        """Parse the first packet of a byte stream.

        Bytes before the first sync byte (0x55) are dropped; on a CRC error only the sync byte is skipped, so parsing
        resynchronizes on the next packet. Call it again on the remaining buffer until it returns INCOMPLETE.

        Args:
            buf: Bytes read from the module.
            on_error: Called with HEADER_CRC_ERROR, DATA_CRC_ERROR or MALFORMED_PACKET on errors.

        Returns:
            (PARSE_RESULT, the remaining bytes, the packet or None): OK with a packet, INCOMPLETE if more bytes are
            needed, CRC_MISMATCH if corrupted bytes were skipped.
        """
        # If the buffer doesn't contain 0x55 (start char)
        # the message isn't needed -> ignore
        if 0x55 not in buf:
            return PARSE_RESULT.INCOMPLETE, [], None

        # Valid buffer starts from 0x55
        buf = list(buf)
        buf = buf[buf.index(0x55) :]

        # Sync byte + 4 header bytes + header CRC
        if len(buf) < 6:
            return PARSE_RESULT.INCOMPLETE, buf, None

        # Check the header CRC before trusting the lengths it announces: a stray 0x55 or a corrupted header
        # would otherwise make us wait for, and then drop, bytes belonging to the following valid packets.
        if buf[5] != crc8.calc(buf[1:5]):
            # Expected on a noisy line: every stray 0x55 lands here while resynchronizing
            Packet.logger.debug('Header CRC error, resynchronizing.')
            if on_error:
                on_error(HEADER_CRC_ERROR)
            # Skip only the sync byte and resynchronize on the next 0x55
            return PARSE_RESULT.CRC_MISMATCH, buf[1:], None

        data_len = (buf[1] << 8) | buf[2]
        opt_len = buf[3]

        # Header: 6 bytes, data, optional data and data checksum
        msg_len = 6 + data_len + opt_len + 1
        if len(buf) < msg_len:
            # If buffer isn't long enough, the message is incomplete
            return PARSE_RESULT.INCOMPLETE, buf, None

        msg = buf[0:msg_len]
        packet_type = msg[4]
        data = msg[6 : 6 + data_len]
        opt_data = msg[6 + data_len : 6 + data_len + opt_len]

        if msg[-1] != crc8.calc(msg[6:-1]):
            Packet.logger.warning(
                'Data CRC error on a %d byte packet (type 0x%02X), dropping it.',
                msg_len,
                packet_type,
                extra={'packet_type': packet_type},
            )
            if on_error:
                on_error(DATA_CRC_ERROR)
            # The message may be a truncated packet running into the next one: skip only the sync byte
            return PARSE_RESULT.CRC_MISMATCH, buf[1:], None

        buf = buf[msg_len:]

        packet_class = Packet
        if packet_type == PACKET.RADIO_ERP1:
            # Need to handle UTE Teach-in here, as it's a separate packet type...
            packet_class = UTETeachInPacket if data and data[0] == RORG.UTE else RadioPacket
        elif packet_type == PACKET.RESPONSE:
            packet_class = ResponsePacket
        elif packet_type == PACKET.EVENT:
            packet_class = EventPacket

        try:
            packet = packet_class(packet_type, data, opt_data)
        except (IndexError, ValueError):
            # Valid on the wire, but too short for what its type requires: keep the raw bytes
            Packet.logger.warning('Malformed %s packet, returning it unparsed.', packet_class.__name__, exc_info=True)
            packet = Packet(packet_type, data, opt_data)
            if on_error:
                on_error(MALFORMED_PACKET)

        packet.received = datetime.datetime.now(datetime.timezone.utc)

        return PARSE_RESULT.OK, buf, packet

    @staticmethod
    def create(
        packet_type: int,
        rorg: int,
        rorg_func: int,
        rorg_type: int,
        direction: int | None = None,
        command: int | None = None,
        destination: list[int] | None = None,
        sender: list[int] | None = None,
        learn: bool = False,
        **kwargs: Any,
    ) -> 'Packet':
        """Build a radio telegram from the field values of its profile.

        Args:
            packet_type: Only PACKET.RADIO_ERP1 is supported.
            rorg: The telegram type: RORG.RPS, BS1, BS4 or VLD.
            rorg_func: The profile's FUNC.
            rorg_type: The profile's TYPE.
            direction: The direction, for profiles with direction-specific layouts.
            command: The command, for profiles with several commands (e.g. D2-01-12).
            destination: The recipient's ID; broadcast (FF:FF:FF:FF) by default.
            sender: The ID to send from, e.g. the module's base ID; DE:AD:BE:EF by default.
            learn: For 1BS and 4BS telegrams, send a teach-in telegram (learn bit).
            **kwargs: The field values by shortcut: raw ints, enum descriptions or their labels, numbers for values
                (see EEP().describe()).

        Returns:
            The packet, decoded as it will be received.

        Raises:
            ValueError: Unsupported packet type or RORG, invalid sender or destination, unknown enum value, or unknown
                VLD profile.
        """
        if packet_type != PACKET.RADIO_ERP1:
            # At least for now, only support PACKET.RADIO_ERP1.
            raise ValueError('Packet type not supported by this function.')

        if rorg not in [RORG.RPS, RORG.BS1, RORG.BS4, RORG.VLD]:
            # At least for now, only support these RORGS.
            raise ValueError('RORG not supported by this function.')

        if destination is None:
            Packet.logger.debug('Replacing destination with broadcast address.')
            destination = [0xFF, 0xFF, 0xFF, 0xFF]

        # TODO: Should use the correct Base ID as default.
        #       Might want to change the sender to be an offset from the actual address?
        if sender is None:
            Packet.logger.debug('Replacing sender with default address.')
            sender = [0xDE, 0xAD, 0xBE, 0xEF]

        if not isinstance(destination, list) or len(destination) != 4:
            raise ValueError('Destination must a list containing 4 (numeric) values.')

        if not isinstance(sender, list) or len(sender) != 4:
            raise ValueError('Sender must a list containing 4 (numeric) values.')

        packet = Packet(packet_type, data=[], optional=[])
        packet.rorg = rorg
        packet.data = [packet.rorg]
        # Select EEP at this point, so we know how many bits we're dealing with (for VLD).
        packet.select_eep(rorg_func, rorg_type, direction, command)
        packet._select_variant_for(kwargs)

        # Initialize data depending on the profile.
        if rorg in [RORG.RPS, RORG.BS1]:
            packet.data.extend([0])
        elif rorg == RORG.BS4:
            packet.data.extend([0, 0, 0, 0])
        else:
            if packet._profile is None:
                raise ValueError('Unknown EEP profile, cannot determine the telegram length.')
            packet.data.extend([0] * int(packet._profile.get('bits', '1')))
        packet.data.extend(sender)
        packet.data.extend([0])
        # Always use sub-telegram 3, maximum dbm (as per spec, when sending),
        # and no security (security not supported as per EnOcean Serial Protocol).
        packet.optional = [3] + destination + [0xFF] + [0]

        command_field = packet._command_field(rorg, rorg_func, rorg_type) if command is not None else None
        if command is not None and not isinstance(command_field, Element):
            kwargs[command_field or 'CMD'] = command

        packet.set_eep(kwargs)
        if command is not None and isinstance(command_field, Element):
            packet._bit_data = EEP._set_raw(command_field, command, packet._bit_data)
        packet._apply_conditions(kwargs)
        if rorg in [RORG.BS1, RORG.BS4] and not learn:
            if rorg == RORG.BS1:
                packet.data[1] |= 1 << 3
            if rorg == RORG.BS4:
                packet.data[4] |= 1 << 3
        packet.data[-1] = packet.status

        # Parse the built packet, so it corresponds to the received packages
        # For example, stuff like RadioPacket.learn should be set.
        parsed_packet = Packet.parse_msg(packet.build())[2]
        assert parsed_packet is not None, 'a packet we just built must parse'
        parsed_packet.received = None
        parsed_packet.rorg = rorg
        # Decoded like a received telegram: the variant is recognized from its conditions
        parsed_packet.parse_eep(rorg_func, rorg_type, direction, None if packet._has_conditions() else command)
        return parsed_packet

    def _apply_conditions(self, given: Mapping[str, Any]) -> None:
        """Set the data and status bits the selected variant requires, so the telegram decodes as that variant.

        Fields given explicitly are left alone (e.g. ECID when several variants share a command).
        """
        if self._profile is None:
            return
        positions = {(tag.get('offset'), tag.get('size')): tag.get('shortcut') for tag in self._profile}
        for condition in self._profile.findall('condition'):
            if positions.get((condition.get('offset'), condition.get('size'))) in given:
                continue
            value = int(condition.get('value', 0))
            if condition.get('source') == 'status':
                self._bit_status = EEP._set_raw(condition, value, self._bit_status)
            else:
                self._bit_data = EEP._set_raw(condition, value, self._bit_data)

    def _select_variant_for(self, values: Mapping[str, Any]) -> None:
        """Select, among the variants sharing the selected one's command, the one matching the values given.

        The most specific one whose condition fields match (e.g. D2-01 command 15 with ECID=1), so create() can build
        any of them.
        """
        if self._profile is None or self._profile.find('condition') is None or self.rorg_func is None:
            return
        profile = self.eep.telegrams[self.rorg][self.rorg_func][self.rorg_type or 0]
        selected = (self._profile.get('command'), self._profile.get('direction'))
        best, best_score = None, -1
        for variant in profile.findall('data'):
            if (variant.get('command'), variant.get('direction')) != selected:
                continue
            fields = {(tag.get('offset'), tag.get('size')): tag.get('shortcut', '') for tag in variant}
            required = {
                fields.get((c.get('offset'), c.get('size')), ''): int(c.get('value', 0))
                for c in variant.findall('condition')
            }
            given = {name: value for name, value in required.items() if isinstance(values.get(name), int)}
            if all(values[name] == value for name, value in given.items()) and len(given) > best_score:
                best, best_score = variant, len(given)
        if best is not None:
            self._profile = best

    def _has_conditions(self) -> bool:
        return self._profile is not None and self._profile.find('condition') is not None

    def _command_field(self, rorg: int, rorg_func: int, rorg_type: int) -> str | Element | None:
        """Where create() writes the command id.

        The shortcut of the selected variant's own command field (named after the profile's <command>, e.g. CMD or
        COM), else the profile-level <command> element itself (for variants without a command field), or None for
        profiles without commands.
        """
        profile = self.eep.telegrams.get(rorg, {}).get(rorg_func, {}).get(rorg_type)
        eep_command = profile.find('command') if profile is not None else None
        if eep_command is None:
            return None
        shortcut = eep_command.get('shortcut', 'CMD')
        if self._profile is not None and any(tag.get('shortcut') == shortcut for tag in self._profile):
            return shortcut
        return eep_command

    def parse(self) -> OrderedDict[str, FieldValue]:
        """Read the fields common to the packet type (e.g. sender, status); called on construction."""
        # Parse status from messages
        if self.rorg in [RORG.RPS, RORG.BS1, RORG.BS4]:
            self.status = self.data[-1]
        if self.rorg == RORG.VLD and self.optional:
            self.status = self.optional[-1]

        if self.rorg in [RORG.RPS, RORG.BS1, RORG.BS4]:
            # These message types should have repeater count in the last for bits of status.
            self.repeater_count = enocean.utils.from_bitarray(self._bit_status[4:])
        return self.parsed

    def select_eep(
        self, rorg_func: int, rorg_type: int, direction: int | None = None, command: int | None = None
    ) -> bool:
        """Select the profile (and its variant) to decode or encode the telegram with.

        Args:
            rorg_func: The profile's FUNC (the RORG is the telegram's).
            rorg_type: The profile's TYPE.
            direction: The direction, for profiles with direction-specific layouts.
            command: The command variant; by default it is recognized from the telegram.

        Returns:
            Whether the profile is known.
        """
        # set EEP profile
        self.rorg_func = rorg_func
        self.rorg_type = rorg_type
        self._profile = self.eep.find_profile(
            self._bit_data, self.rorg, rorg_func, rorg_type, direction, command, self._bit_status
        )
        return self._profile is not None

    def parse_eep(
        self,
        rorg_func: int | None = None,
        rorg_type: int | None = None,
        direction: int | None = None,
        command: int | None = None,
    ) -> list[str]:
        """Decode the telegram's fields into `parsed`.

        Args:
            rorg_func: The profile's FUNC; if omitted, the profile selected before (select_eep()) is used.
            rorg_type: The profile's TYPE.
            direction: See select_eep().
            command: See select_eep().

        Returns:
            The shortcuts of the decoded fields.
        """
        # set EEP profile, if demanded
        if rorg_func is not None and rorg_type is not None:
            self.select_eep(rorg_func, rorg_type, direction, command)
        # parse data
        provides, values = self.eep.get_values(self._profile, self._bit_data, self._bit_status)
        self.parsed.update(values)
        return list(provides)

    def set_eep(self, data: dict[str, Any]) -> None:
        """Encode field values, by shortcut, into the telegram with the selected profile."""
        self._bit_data, self._bit_status = self.eep.set_values(self._profile, self._bit_data, self._bit_status, data)

    @property
    def eep_id(self) -> EEPId | None:
        """The profile selected with select_eep()/parse_eep() (or announced by a teach-in telegram), if any."""
        if self.rorg_func is None or self.rorg_type is None or self.rorg == RORG.UNDEFINED:
            return None
        return EEPId(self.rorg, self.rorg_func, self.rorg_type)

    @property
    def command(self) -> int | None:
        """Command of the selected profile variant, for profiles with several commands (e.g. D2-01-12)."""
        if self._profile is None or self._profile.get('command') is None:
            return None
        return int(self._profile.get('command', 0))

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable view of the packet.

        Hex strings for bytes and IDs, enum names (hex for unknown values), ISO 8601 reception time and, once decoded,
        the EEP and field values.
        """
        return {
            'packet_type': enum_name(PACKET, self.packet_type),
            'received': self.received.isoformat() if self.received else None,
            'data': enocean.utils.to_hex_string(self.data),
            'optional': enocean.utils.to_hex_string(self.optional),
        }

    def build(self) -> list[int]:
        """The packet's ESP3 bytes, with header and CRCs, as written to the module."""
        data_length = len(self.data)
        ords = [0x55, (data_length >> 8) & 0xFF, data_length & 0xFF, len(self.optional), int(self.packet_type)]
        ords.append(crc8.calc(ords[1:5]))
        ords.extend(self.data)
        ords.extend(self.optional)
        ords.append(crc8.calc(ords[6:]))
        return ords


class RadioPacket(Packet):
    """A radio telegram (ERP1).

    Attributes set when parsing: `sender` / `destination` (4-byte IDs, also as `sender_hex` / `destination_hex`),
    `dbm` (signal strength of the received telegram, None if the module didn't report it) and `learn`.

    `learn` tells whether the telegram can be used to teach the device in. 1BS and 4BS telegrams carry a learn bit,
    UTE telegrams a teach-in request; RPS and VLD telegrams have no learn bit, so `learn` is always True for them:
    any of their telegrams may be used to teach the device in (e.g. pressing a rocker switch).
    """

    destination: list[int] = [0xFF, 0xFF, 0xFF, 0xFF]
    # Set by DeviceRegistry.decode() when the sender is a known device
    device: 'Device | None' = None
    dbm: int | None = None
    sender: list[int] = [0xFF, 0xFF, 0xFF, 0xFF]
    learn = True
    contains_eep = False

    def __str__(self) -> str:
        packet_str = super().__str__()
        return '%s->%s (%s dBm): %s' % (self.sender_hex, self.destination_hex, self.dbm, packet_str)

    @property
    def dBm(self) -> int:  # noqa: N802
        """Deprecated: use dbm (None instead of 0 when the module didn't report the signal strength)."""
        warnings.warn('RadioPacket.dBm is deprecated, use dbm', DeprecationWarning, stacklevel=2)
        return self.dbm or 0

    @staticmethod
    def create(  # type: ignore[override]
        rorg: int,
        rorg_func: int,
        rorg_type: int,
        direction: int | None = None,
        command: int | None = None,
        destination: list[int] | None = None,
        sender: list[int] | None = None,
        learn: bool = False,
        **kwargs: Any,
    ) -> 'RadioPacket':
        """Build a radio telegram (ERP1): see Packet.create(), without its packet_type argument."""
        packet = Packet.create(
            PACKET.RADIO_ERP1, rorg, rorg_func, rorg_type, direction, command, destination, sender, learn, **kwargs
        )
        assert isinstance(packet, RadioPacket)
        return packet

    def to_dict(self) -> dict[str, Any]:
        """See Packet.to_dict(); adds the radio fields, the EEP, the decoded values and the device."""
        eep_id = self.eep_id
        return {
            **super().to_dict(),
            'rorg': enum_name(RORG, self.rorg),
            'sender': self.sender_hex,
            'destination': self.destination_hex,
            'dbm': self.dbm,
            'status': self.status,
            'repeater_count': self.repeater_count,
            'learn': self.learn,
            'eep': str(eep_id) if eep_id else None,
            'command': self.command,
            'values': {shortcut: dict(field) for shortcut, field in self.parsed.items()},
            'device': self.device.to_dict() if self.device else None,
        }

    @property
    def sender_int(self) -> int:
        """The sender's ID as an integer."""
        return enocean.utils.combine_hex(self.sender)

    @property
    def sender_hex(self) -> str:
        """The sender's ID as text, e.g. '05:99:77:AF'."""
        return enocean.utils.to_hex_string(self.sender)

    @property
    def destination_int(self) -> int:
        """The destination ID as an integer."""
        return enocean.utils.combine_hex(self.destination)

    @property
    def destination_hex(self) -> str:
        """The destination ID as text; 'FF:FF:FF:FF' for broadcast telegrams."""
        return enocean.utils.to_hex_string(self.destination)

    def parse(self) -> OrderedDict[str, FieldValue]:
        """Read sender, destination, signal strength and learn bit; see Packet.parse()."""
        # Optional data (sub-telegram count, destination, dBm, security level) may be omitted
        if len(self.optional) >= 6:
            self.destination = self.optional[1:5]
            self.dbm = -self.optional[5]
        self.sender = self.data[-5:-1]
        # RPS and VLD have no learn bit: any of their telegrams may be used for teach-in
        self.learn = True

        self.rorg = self.data[0]

        # parse learn bit and FUNC/TYPE, if applicable
        if self.rorg == RORG.BS1:
            self.learn = not self._bit_data[DB0.BIT_3]
        if self.rorg == RORG.BS4:
            self.learn = not self._bit_data[DB0.BIT_3]
            if self.learn:
                self.contains_eep = self._bit_data[DB0.BIT_7]
                if self.contains_eep:
                    # Get rorg_func and rorg_type from an unidirectional learn packet
                    self.rorg_func = enocean.utils.from_bitarray(self._bit_data[DB3.BIT_7 : DB3.BIT_1])
                    self.rorg_type = enocean.utils.from_bitarray(self._bit_data[DB3.BIT_1 : DB2.BIT_2])
                    self.rorg_manufacturer = enocean.utils.from_bitarray(self._bit_data[DB2.BIT_2 : DB0.BIT_7])
                    self.logger.debug(
                        'learn received, EEP detected, RORG: 0x%02X, FUNC: 0x%02X, TYPE: 0x%02X, Manufacturer: 0x%02X',
                        self.rorg,
                        self.rorg_func,
                        self.rorg_type,
                        self.rorg_manufacturer,
                    )

        return super().parse()


class UTETeachInPacket(RadioPacket):
    """A Universal Teach-in (UTE) request: a device asking to be taught in (or out), announcing its profile.

    Communicators answer them (see Communicator.learn()); `eep_id` is the announced profile.
    """

    # Request types
    TEACH_IN = 0b00
    DELETE = 0b01
    NOT_SPECIFIC = 0b10

    # Response types
    NOT_ACCEPTED = [False, False]
    TEACHIN_ACCEPTED = [False, True]
    DELETE_ACCEPTED = [True, False]
    EEP_NOT_SUPPORTED = [True, True]

    unidirectional = False
    response_expected = False
    number_of_channels = 0xFF
    rorg_of_eep: int = RORG.UNDEFINED
    request_type = NOT_SPECIFIC

    contains_eep = True

    @property
    def eep_id(self) -> EEPId | None:
        """The profile the device announces in its teach-in request."""
        if self.rorg_func is None or self.rorg_type is None:
            return None
        return EEPId(self.rorg_of_eep, self.rorg_func, self.rorg_type)

    def to_dict(self) -> dict[str, Any]:
        """See RadioPacket.to_dict(); adds the teach-in request fields."""
        return {
            **super().to_dict(),
            'teach_in': {
                'request': {self.TEACH_IN: 'teach_in', self.DELETE: 'delete'}.get(self.request_type, 'not_specific'),
                'bidirectional': self.bidirectional,
                'response_expected': self.response_expected,
                'number_of_channels': self.number_of_channels,
                'manufacturer': self.rorg_manufacturer,
            },
        }

    @property
    def channel(self) -> int:
        """Deprecated alias of number_of_channels."""
        warnings.warn(
            'UTETeachInPacket.channel is deprecated, use number_of_channels', DeprecationWarning, stacklevel=2
        )
        return self.number_of_channels

    @property
    def bidirectional(self) -> bool:
        """Whether the device expects bidirectional communication."""
        return not self.unidirectional

    @property
    def teach_in(self) -> bool:
        """Whether the request may be a teach-in (a teach-in or a not-specific request)."""
        return self.request_type != self.DELETE

    @property
    def delete(self) -> bool:
        """Whether the request is a deletion (teach-out)."""
        return self.request_type == self.DELETE

    def parse(self) -> OrderedDict[str, FieldValue]:
        """Read the request: type, announced profile, manufacturer, channels."""
        super().parse()
        self.unidirectional = not self._bit_data[DB6.BIT_7]
        self.response_expected = not self._bit_data[DB6.BIT_6]
        self.request_type = enocean.utils.from_bitarray(self._bit_data[DB6.BIT_5 : DB6.BIT_3])
        self.rorg_manufacturer = enocean.utils.from_bitarray(
            self._bit_data[DB3.BIT_2 : DB2.BIT_7] + self._bit_data[DB4.BIT_7 : DB3.BIT_7]
        )  # noqa: E501
        # Number of channels to teach in (0xFF: all)
        self.number_of_channels = self.data[2]
        self.rorg_type = self.data[5]
        self.rorg_func = self.data[6]
        self.rorg_of_eep = self.data[7]
        if self.teach_in:
            self.learn = True
        return self.parsed

    def create_response_packet(self, sender_id: list[int], response: list[bool] = TEACHIN_ACCEPTED) -> RadioPacket:
        """The UTE response to this request.

        Args:
            sender_id: The ID to answer from, usually the module's base ID.
            response: TEACHIN_ACCEPTED, DELETE_ACCEPTED, EEP_NOT_SUPPORTED or NOT_ACCEPTED.

        Returns:
            The response packet, addressed to the requesting device.
        """
        # Create data:
        # - Respond with same RORG (UTE Teach-in)
        # - Always use bidirectional communication, set response code, set command identifier.
        # - Databytes 5 to 0 are copied from the original message
        # - Set sender id and status
        data = (
            [self.rorg]
            + [enocean.utils.from_bitarray([True, False] + response + [False, False, False, True])]
            + self.data[2:8]
            + sender_id
            + [0]
        )

        # Always use 0x03 to indicate sending, attach sender ID, dBm, and security level
        optional = [0x03] + self.sender + [0xFF, 0x00]

        return RadioPacket(PACKET.RADIO_ERP1, data=data, optional=optional)


class ResponsePacket(Packet):
    """The module's response to a command: `response` is the return code (RETURN_CODE), `response_data` the rest."""

    response = 0
    response_data: list[int] = []

    def parse(self) -> OrderedDict[str, FieldValue]:
        """Read the return code and the response data."""
        self.response = self.data[0]
        self.response_data = self.data[1:]
        return super().parse()

    def to_dict(self) -> dict[str, Any]:
        """See Packet.to_dict(); adds the return code and response data."""
        return {
            **super().to_dict(),
            'return_code': enum_name(RETURN_CODE, self.response),
            'response_data': enocean.utils.to_hex_string(self.response_data),
        }


class EventPacket(Packet):
    """An event reported by the module: `event` is the event code (EVENT_CODE), `event_data` the rest."""

    event = 0
    event_data: list[int] = []

    def parse(self) -> OrderedDict[str, FieldValue]:
        """Read the event code and data."""
        self.event = self.data[0]
        self.event_data = self.data[1:]
        return super().parse()

    def to_dict(self) -> dict[str, Any]:
        """See Packet.to_dict(); adds the event code and data."""
        return {
            **super().to_dict(),
            'event_code': enum_name(EVENT_CODE, self.event),
            'event_data': enocean.utils.to_hex_string(self.event_data),
        }
