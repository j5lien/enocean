import datetime
import logging
from collections import OrderedDict
from collections.abc import Callable
from typing import Any
from xml.etree.ElementTree import Element

import enocean.utils
from enocean.protocol import crc8
from enocean.protocol.constants import DB0, DB2, DB3, DB4, DB6, PACKET, PARSE_RESULT, RORG
from enocean.protocol.eep import EEP, FieldValue

# Kinds of errors reported to Packet.parse_msg(on_error=...)
HEADER_CRC_ERROR = 'header_crc'
DATA_CRC_ERROR = 'data_crc'
MALFORMED_PACKET = 'malformed'


class Packet:
    """
    Base class for Packet.
    Mainly used for for packet generation and
    Packet.parse_msg(buf) for parsing message.
    parse_msg() returns subclass, if one is defined for the data type.
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
        """
        Parses message from buffer.
        returns:
            - PARSE_RESULT
            - remaining buffer
            - Packet -object (if message was valid, else None)
        on_error, if given, is called with HEADER_CRC_ERROR, DATA_CRC_ERROR or MALFORMED_PACKET.
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
        """
        Creates an packet ready for sending.
        Uses rorg, rorg_func and rorg_type to determine the values set based on EEP.
        Additional arguments (**kwargs) are used for setting the values.

        Currently only supports:
            - PACKET.RADIO_ERP1
            - RORGs RPS, BS1, BS4, VLD.

        TODO:
            - Require sender to be set? Would force the "correct" sender to be set.
            - Do we need to set telegram control bits?
              Might be useful for acting as a repeater?
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

        if command:
            # Set CMD to command, if applicable.. Helps with VLD.
            kwargs['CMD'] = command

        packet.set_eep(kwargs)
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
        parsed_packet.rorg = rorg
        parsed_packet.parse_eep(rorg_func, rorg_type, direction, command)
        return parsed_packet

    def parse(self) -> OrderedDict[str, FieldValue]:
        """Parse data from Packet"""
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
        """Set EEP based on FUNC and TYPE"""
        # set EEP profile
        self.rorg_func = rorg_func
        self.rorg_type = rorg_type
        self._profile = self.eep.find_profile(self._bit_data, self.rorg, rorg_func, rorg_type, direction, command)
        return self._profile is not None

    def parse_eep(
        self,
        rorg_func: int | None = None,
        rorg_type: int | None = None,
        direction: int | None = None,
        command: int | None = None,
    ) -> list[str]:
        """Parse EEP based on FUNC and TYPE"""
        # set EEP profile, if demanded
        if rorg_func is not None and rorg_type is not None:
            self.select_eep(rorg_func, rorg_type, direction, command)
        # parse data
        provides, values = self.eep.get_values(self._profile, self._bit_data, self._bit_status)
        self.parsed.update(values)
        return list(provides)

    def set_eep(self, data: dict[str, Any]) -> None:
        """Update packet data based on EEP. Input data is a dictionary with keys corresponding to the EEP."""
        self._bit_data, self._bit_status = self.eep.set_values(self._profile, self._bit_data, self._bit_status, data)

    def build(self) -> list[int]:
        """Build Packet for sending to EnOcean controller"""
        data_length = len(self.data)
        ords = [0x55, (data_length >> 8) & 0xFF, data_length & 0xFF, len(self.optional), int(self.packet_type)]
        ords.append(crc8.calc(ords[1:5]))
        ords.extend(self.data)
        ords.extend(self.optional)
        ords.append(crc8.calc(ords[6:]))
        return ords


class RadioPacket(Packet):
    destination: list[int] = [0xFF, 0xFF, 0xFF, 0xFF]
    dBm = 0
    sender: list[int] = [0xFF, 0xFF, 0xFF, 0xFF]
    learn = True
    contains_eep = False

    def __str__(self) -> str:
        packet_str = super().__str__()
        return '%s->%s (%d dBm): %s' % (self.sender_hex, self.destination_hex, self.dBm, packet_str)

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
        packet = Packet.create(
            PACKET.RADIO_ERP1, rorg, rorg_func, rorg_type, direction, command, destination, sender, learn, **kwargs
        )
        assert isinstance(packet, RadioPacket)
        return packet

    @property
    def sender_int(self) -> int:
        return enocean.utils.combine_hex(self.sender)

    @property
    def sender_hex(self) -> str:
        return enocean.utils.to_hex_string(self.sender)

    @property
    def destination_int(self) -> int:
        return enocean.utils.combine_hex(self.destination)

    @property
    def destination_hex(self) -> str:
        return enocean.utils.to_hex_string(self.destination)

    def parse(self) -> OrderedDict[str, FieldValue]:
        # Optional data (sub-telegram count, destination, dBm, security level) may be omitted
        if len(self.optional) >= 6:
            self.destination = self.optional[1:5]
            self.dBm = -self.optional[5]
        self.sender = self.data[-5:-1]
        # Default to learn == True, as some devices don't have a learn button
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
    channel: int | None = None

    contains_eep = True

    @property
    def bidirectional(self) -> bool:
        return not self.unidirectional

    @property
    def teach_in(self) -> bool:
        return self.request_type != self.DELETE

    @property
    def delete(self) -> bool:
        return self.request_type == self.DELETE

    def parse(self) -> OrderedDict[str, FieldValue]:
        super().parse()
        self.unidirectional = not self._bit_data[DB6.BIT_7]
        self.response_expected = not self._bit_data[DB6.BIT_6]
        self.request_type = enocean.utils.from_bitarray(self._bit_data[DB6.BIT_5 : DB6.BIT_3])
        self.rorg_manufacturer = enocean.utils.from_bitarray(
            self._bit_data[DB3.BIT_2 : DB2.BIT_7] + self._bit_data[DB4.BIT_7 : DB3.BIT_7]
        )  # noqa: E501
        self.channel = self.data[2]
        self.rorg_type = self.data[5]
        self.rorg_func = self.data[6]
        self.rorg_of_eep = self.data[7]
        if self.teach_in:
            self.learn = True
        return self.parsed

    def create_response_packet(self, sender_id: list[int], response: list[bool] = TEACHIN_ACCEPTED) -> RadioPacket:
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
    response = 0
    response_data: list[int] = []

    def parse(self) -> OrderedDict[str, FieldValue]:
        self.response = self.data[0]
        self.response_data = self.data[1:]
        return super().parse()


class EventPacket(Packet):
    event = 0
    event_data: list[int] = []

    def parse(self) -> OrderedDict[str, FieldValue]:
        self.event = self.data[0]
        self.event_data = self.data[1:]
        return super().parse()
