import logging
import os
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, TypedDict
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


@dataclass(frozen=True, order=True)
class EEPId:
    """An EnOcean Equipment Profile, e.g. D2-01-12: RORG 0xD2, FUNC 0x01, TYPE 0x12."""

    rorg: int
    func: int
    type: int

    @classmethod
    def parse(cls, value: 'str | EEPId') -> 'EEPId':
        """Parses 'D2-01-12' (case-insensitive, '-' or ':' separated); EEPId instances are returned unchanged."""
        if isinstance(value, EEPId):
            return value
        parts = value.replace(':', '-').split('-')
        if len(parts) != 3:
            raise ValueError('Invalid EEP %r, expected RORG-FUNC-TYPE such as D2-01-12' % value)
        rorg, func, type_ = (int(part, 16) for part in parts)
        return cls(rorg, func, type_)

    def __str__(self) -> str:
        return '%02X-%02X-%02X' % (self.rorg, self.func, self.type)


class FieldValue(TypedDict):
    """A decoded EEP field, as found in Packet.parsed."""

    description: str | None
    unit: str
    value: Any
    raw_value: int | None


def _attr(element: Element, name: str) -> str:
    return element.attrib[name]


def _child(element: Element, tag: str) -> Element:
    child = element.find(tag)
    if child is None:
        raise KeyError('<%s> has no <%s>' % (element.tag, tag))
    return child


def _float_text(element: Element, path: str) -> float:
    return float(_child(element, path).text or '')


def _range_and_scale(element: Element) -> tuple[float, float, float, float]:
    rng, scl = _child(element, 'range'), _child(element, 'scale')
    return _float_text(rng, 'min'), _float_text(rng, 'max'), _float_text(scl, 'min'), _float_text(scl, 'max')


@dataclass(frozen=True)
class FieldDescription:
    """One field of a profile variant, as defined in EEP.xml."""

    shortcut: str
    description: str | None
    # 'value' (linear raw -> scaled number), 'enum' (raw -> description) or 'status' (bit of the status byte)
    kind: str
    offset: int
    size: int
    unit: str
    # value fields: raw range and the scaled range it maps to
    raw_range: tuple[float, float] | None = None
    scale: tuple[float, float] | None = None
    # enum fields: descriptions by raw value, and (start, end, description) raw value ranges
    items: Mapping[int, str] = field(default_factory=dict)
    ranges: tuple[tuple[int, int, str], ...] = ()


@dataclass(frozen=True)
class ProfileDescription:
    """One variant (per direction or command) of a profile."""

    eep_id: EEPId
    description: str | None
    function: str | None
    direction: int | None
    command: int | None
    # Telegram payload length in bytes, for VLD profiles
    length: int | None
    fields: tuple[FieldDescription, ...]

    def field(self, shortcut: str) -> FieldDescription:
        return next(f for f in self.fields if f.shortcut == shortcut)


def _describe_field(tag: Element) -> FieldDescription:
    raw_range = scale = None
    if tag.tag == 'value':
        rng_min, rng_max, scl_min, scl_max = _range_and_scale(tag)
        raw_range, scale = (rng_min, rng_max), (scl_min, scl_max)
    return FieldDescription(
        shortcut=_attr(tag, 'shortcut'),
        description=tag.get('description'),
        kind=tag.tag,
        offset=int(_attr(tag, 'offset')),
        size=int(_attr(tag, 'size')),
        unit=tag.get('unit', ''),
        raw_range=raw_range,
        scale=scale,
        items={int(_attr(item, 'value')): item.get('description', '') for item in tag.findall('item')},
        ranges=tuple(
            (int(_attr(item, 'start')), int(_attr(item, 'end')), item.get('description', ''))
            for item in tag.findall('rangeitem')
        ),
    )


class EEP:
    logger = logging.getLogger('enocean.protocol.eep')

    def __init__(self) -> None:
        self.init_ok = False
        self.telegrams: dict[int, dict[int, dict[int, Element]]] = {}

        eep_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'EEP.xml')
        try:
            self.xml_root = ElementTree.parse(eep_path).getroot()
            self.init_ok = True
            self.__load_xml()
        except (OSError, ElementTree.ParseError):
            # Impossible to test with the current structure?
            # To be honest, as the XML is included with the library,
            # there should be no possibility of ever reaching this...
            self.logger.warning('Cannot load protocol file!')
            self.init_ok = False

    def __load_xml(self) -> None:
        self.telegrams = {
            int(_attr(telegram, 'rorg'), 16): {
                int(_attr(function, 'func'), 16): {
                    int(_attr(type, 'type'), 16): type for type in function.iter('profile')
                }
                for function in telegram.iter('profiles')
            }
            for telegram in self.xml_root.iter('telegram')
        }

    @staticmethod
    def _find_child(source: Element, tag: str, **attributes: object) -> Element | None:
        """First child element with the given tag and attribute values (compared as strings), or None."""
        for child in source.findall(tag):
            if all(child.get(name) == str(value) for name, value in attributes.items()):
                return child
        return None

    @staticmethod
    def _get_raw(source: Element, bitarray: list[bool]) -> int | None:
        """Get raw data as integer, based on offset and size"""
        offset = int(_attr(source, 'offset'))
        size = int(_attr(source, 'size'))
        length = len(bitarray)

        if offset >= length:
            return None

        end = min(length, offset + size)
        return int(''.join(['1' if digit else '0' for digit in bitarray[offset:end]]), 2)

    @staticmethod
    def _set_raw(target: Element, raw_value: int, bitarray: list[bool]) -> list[bool]:
        """put value into bit array"""
        offset = int(_attr(target, 'offset'))
        size = int(_attr(target, 'size'))
        for digit in range(size):
            bitarray[offset + digit] = (raw_value >> (size - digit - 1)) & 0x01 != 0
        return bitarray

    @staticmethod
    def _get_rangeitem(source: Element, raw_value: int) -> Element | None:
        for rangeitem in source.findall('rangeitem'):
            if raw_value in range(int(rangeitem.get('start', -1)), int(rangeitem.get('end', -1)) + 1):
                return rangeitem
        return None

    def _get_value(self, source: Element, raw_value: int) -> dict[str, FieldValue]:
        """Get value, based on the data in XML"""
        rng_min, rng_max, scl_min, scl_max = _range_and_scale(source)

        return {
            _attr(source, 'shortcut'): {
                'description': source.get('description'),
                'unit': source.attrib['unit'],
                'value': (scl_max - scl_min) / (rng_max - rng_min) * (raw_value - rng_min) + scl_min,
                'raw_value': raw_value,
            }
        }

    def _get_enum(self, source: Element, raw_value: int) -> dict[str, FieldValue]:
        """Get enum value, based on the data in XML"""
        # Find value description.
        value_desc = self._find_child(source, 'item', value=raw_value)
        if value_desc is None:
            value_desc = self._get_rangeitem(source, raw_value)

        unit = source.get('unit', '')
        value: Any
        if value_desc is not None and value_desc.get('scale-min') is not None:
            # A range of raw values standing for a physical value (e.g. 1..15 -> 0.5..7.5 s)
            start, end = int(_attr(value_desc, 'start')), int(_attr(value_desc, 'end'))
            scl_min, scl_max = float(_attr(value_desc, 'scale-min')), float(_attr(value_desc, 'scale-max'))
            value = scl_min + (raw_value - start) * (scl_max - scl_min) / (end - start) if end != start else scl_min
            unit = value_desc.get('unit', unit)
        else:
            description = value_desc.get('description') if value_desc is not None else None
            value = description.format(value=raw_value) if description else ''
        return {
            _attr(source, 'shortcut'): {
                'description': source.get('description'),
                'unit': unit,
                'value': value,
                'raw_value': raw_value,
            }
        }

    def _get_boolean(self, source: Element, bitarray: list[bool]) -> dict[str, FieldValue]:
        """Get boolean value, based on the data in XML"""
        raw_value = self._get_raw(source, bitarray)
        return {
            _attr(source, 'shortcut'): {
                'description': source.get('description'),
                'unit': source.get('unit', ''),
                'value': bool(raw_value),
                'raw_value': raw_value,
            }
        }

    def _set_value(self, target: Element, value: float, bitarray: list[bool]) -> list[bool]:
        """set given numeric value to target field in bitarray"""
        # derive raw value
        rng_min, rng_max, scl_min, scl_max = _range_and_scale(target)
        raw_value = (value - scl_min) * (rng_max - rng_min) / (scl_max - scl_min) + rng_min
        # store value in bitfield
        return self._set_raw(target, int(raw_value), bitarray)

    def _set_enum(self, target: Element, value: int | float | str, bitarray: list[bool]) -> list[bool]:
        """
        Set an enum field in bitarray: by raw value (int), by description (str), or by physical value (float) for
        ranges with a scale.
        """
        if isinstance(value, float):
            for rangeitem in target.findall('rangeitem'):
                if rangeitem.get('scale-min') is None:
                    continue
                start, end = int(_attr(rangeitem, 'start')), int(_attr(rangeitem, 'end'))
                scl_min, scl_max = float(_attr(rangeitem, 'scale-min')), float(_attr(rangeitem, 'scale-max'))
                if min(scl_min, scl_max) <= value <= max(scl_min, scl_max):
                    raw = (
                        start + (value - scl_min) * (end - start) / (scl_max - scl_min) if scl_max != scl_min else start
                    )
                    return self._set_raw(target, round(raw), bitarray)
            raise ValueError('Value %s is outside the scaled ranges of %s.' % (value, target.get('shortcut')))
        if isinstance(value, int):
            # check whether this value exists
            if (
                self._find_child(target, 'item', value=value) is not None
                or self._get_rangeitem(target, value) is not None
            ):
                # set integer values directly
                raw_value = value
            else:
                raise ValueError('Enum value "%s" not found in EEP.' % (value))
        else:
            value_item = self._find_child(target, 'item', description=value)
            if value_item is None:
                # Official descriptions are long ('Button AI: "Switch light on" or ...'): accept their label, the part
                # before the colon, when unambiguous
                label = str(value).strip().lower()
                matching = [
                    item
                    for item in target.findall('item')
                    if item.get('description', '').split(':')[0].strip().lower() == label
                ]
                if len(matching) != 1:
                    raise ValueError('Enum description for value "%s" not found in EEP.' % (value))
                value_item = matching[0]
            raw_value = int(_attr(value_item, 'value'))
        return self._set_raw(target, raw_value, bitarray)

    @staticmethod
    def _set_boolean(target: Element, data: bool, bitarray: list[bool]) -> list[bool]:
        """set given value to target bit in bitarray"""
        bitarray[int(_attr(target, 'offset'))] = data
        return bitarray

    def profiles(self) -> Iterator[EEPId]:
        """Every profile defined in EEP.xml."""
        for rorg, functions in sorted(self.telegrams.items()):
            for func, types in sorted(functions.items()):
                for type_ in sorted(types):
                    yield EEPId(rorg, func, type_)

    def describe(self, eep_id: EEPId | str) -> tuple[ProfileDescription, ...]:
        """
        The fields of a profile, one ProfileDescription per variant (direction or command), e.g.
        `EEP().describe('D2-01-12')`. Raises KeyError for an unknown profile.
        """
        eep_id = EEPId.parse(eep_id)
        profile = self.telegrams[eep_id.rorg][eep_id.func][eep_id.type]
        function = next(
            (
                f.get('description')
                for telegram in self.xml_root.iter('telegram')
                if int(_attr(telegram, 'rorg'), 16) == eep_id.rorg
                for f in telegram.iter('profiles')
                if int(_attr(f, 'func'), 16) == eep_id.func
            ),
            None,
        )
        return tuple(
            ProfileDescription(
                eep_id=eep_id,
                description=profile.get('description'),
                function=function,
                direction=int(data.get('direction', 0)) if data.get('direction') else None,
                command=int(data.get('command', 0)) if data.get('command') else None,
                length=int(data.get('bits', 0)) if data.get('bits') else None,
                fields=tuple(_describe_field(tag) for tag in data if tag.tag in ('value', 'enum', 'status')),
            )
            for data in profile.findall('data')
        )

    def find_profile(
        self,
        bitarray: list[bool],
        eep_rorg: int,
        rorg_func: int,
        rorg_type: int,
        direction: int | None = None,
        command: int | None = None,
        status: list[bool] | None = None,
    ) -> Element | None:
        """
        The <data> variant of a profile to decode or build a telegram with: the one for `command` or `direction` when
        given, else the one whose conditions the telegram's data bits (bitarray) and status bits match.
        """
        if not self.init_ok:
            self.logger.warning('EEP.xml not loaded!')
            return None

        if eep_rorg not in self.telegrams:
            self.logger.warning('Cannot find rorg %s in EEP!', hex(eep_rorg))
            return None

        if rorg_func not in self.telegrams[eep_rorg]:
            self.logger.warning('Cannot find rorg %s func %s in EEP!', hex(eep_rorg), hex(rorg_func))
            return None

        if rorg_type not in self.telegrams[eep_rorg][rorg_func]:
            self.logger.warning(
                'Cannot find rorg %s func %s type %s in EEP!', hex(eep_rorg), hex(rorg_func), hex(rorg_type)
            )
            return None

        profile = self.telegrams[eep_rorg][rorg_func][rorg_type]

        if command:
            # multiple commands can be defined, with the command id always in same location (per RORG-FUNC-TYPE).
            eep_command = profile.find('command')
            # If commands are not set in EEP, or command is None,
            # get the first data as a "best guess".
            if eep_command is None:
                return profile.find('data')

            # If eep_command is defined, so should be data.command
            return self._find_child(profile, 'data', command=command)

        # extract data description
        # the direction tag is optional
        if direction is None:
            detected = self._detect_variant(profile, bitarray, status)
            if detected is None:
                detected = self._detect_command(profile, bitarray)
            return detected if detected is not None else profile.find('data')
        return self._find_child(profile, 'data', direction=direction)

    @staticmethod
    def _detect_variant(profile: Element, bitarray: list[bool], status: list[bool] | None) -> Element | None:
        """
        The variant whose <condition> elements (data or status bits the telegram must hold) all match, preferring
        variants of the telegram's length, then the most specific one. None if no variant has conditions or none
        matches.
        """
        variants = [data for data in profile.findall('data') if data.find('condition') is not None]
        if not variants or not bitarray:
            return None

        def matches(data: Element) -> bool:
            for condition in data.findall('condition'):
                bits = status if condition.get('source') == 'status' else bitarray
                if bits is None or EEP._get_raw(condition, bits) != int(_attr(condition, 'value')):
                    return False
            return True

        same_length = [data for data in variants if int(data.get('bits', 0)) * 8 == len(bitarray)]
        for candidates in (same_length, variants):
            matching = [data for data in candidates if matches(data)]
            if matching:
                # The most specific variant (e.g. D2-30 command 3 for heating channel 31 over plain command 3)
                return max(matching, key=lambda data: len(data.findall('condition')))
        return None

    @staticmethod
    def _detect_command(profile: Element, bitarray: list[bool]) -> Element | None:
        """
        For profiles with several commands, the <data> variant the telegram actually carries: the one whose own
        command field holds its command number, preferring variants whose length matches the telegram's (the command
        field is not at the same place in every variant, e.g. D2-05-00). None if the profile has no commands or none
        matches.
        """
        eep_command = profile.find('command')
        if eep_command is None or not bitarray:
            return None
        shortcuts = {eep_command.get('shortcut'), 'CMD'}
        variants = [data for data in profile.findall('data') if data.get('command')]
        same_length = [data for data in variants if data.get('bits') and int(data.get('bits', 0)) * 8 == len(bitarray)]
        for candidates in (same_length, variants):
            for data in candidates:
                field = next((tag for tag in data if tag.get('shortcut') in shortcuts), eep_command)
                if EEP._get_raw(field, bitarray) == int(_attr(data, 'command')):
                    return data
        return None

    def get_values(
        self, profile: Element | None, bitarray: list[bool], status: list[bool]
    ) -> tuple[Iterable[str], dict[str, FieldValue]]:
        """Get keys and values from bitarray"""
        if not self.init_ok or profile is None:
            return [], {}

        output: OrderedDict[str, FieldValue] = OrderedDict()
        for source in profile:
            if source.tag in ('value', 'enum'):
                raw_value = self._get_raw(source, bitarray)
                # Skip fields lying beyond the end of a (truncated) telegram
                if raw_value is None:
                    continue
                if source.tag == 'value':
                    output.update(self._get_value(source, raw_value))
                else:
                    output.update(self._get_enum(source, raw_value))
            if source.tag == 'status':
                output.update(self._get_boolean(source, status))
        return output.keys(), output

    def set_values(
        self, profile: Element | None, data: list[bool], status: list[bool], properties: Mapping[str, Any]
    ) -> tuple[list[bool], list[bool]]:
        """Update data based on data contained in properties"""
        if not self.init_ok or profile is None:
            return data, status

        for shortcut, value in properties.items():
            # find the given property from EEP
            target = next((tag for tag in profile.iter() if tag.get('shortcut') == shortcut), None)
            if target is None:
                # TODO: Should we raise an error?
                self.logger.warning('Cannot find data description for shortcut %s', shortcut)
                continue

            # update bit_data
            if target.tag == 'value':
                data = self._set_value(target, value, data)
            if target.tag == 'enum':
                data = self._set_enum(target, value, data)
            if target.tag == 'status':
                status = self._set_boolean(target, value, status)
        return data, status
