import logging
import os
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from typing import Any, TypedDict
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

# Left as a helper
from enocean.protocol.constants import RORG  # noqa: F401


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

        description = value_desc.get('description') if value_desc is not None else None
        return {
            _attr(source, 'shortcut'): {
                'description': source.get('description'),
                'unit': source.get('unit', ''),
                'value': description.format(value=raw_value) if description else '',
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

    def _set_enum(self, target: Element, value: int | str, bitarray: list[bool]) -> list[bool]:
        """set given enum value (by string or integer value) to target field in bitarray"""
        # derive raw value
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
                raise ValueError('Enum description for value "%s" not found in EEP.' % (value))
            raw_value = int(_attr(value_item, 'value'))
        return self._set_raw(target, raw_value, bitarray)

    @staticmethod
    def _set_boolean(target: Element, data: bool, bitarray: list[bool]) -> list[bool]:
        """set given value to target bit in bitarray"""
        bitarray[int(_attr(target, 'offset'))] = data
        return bitarray

    def find_profile(
        self,
        bitarray: list[bool],
        eep_rorg: int,
        rorg_func: int,
        rorg_type: int,
        direction: int | None = None,
        command: int | None = None,
    ) -> Element | None:
        """Find profile and data description, matching RORG, FUNC and TYPE"""
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
            return profile.find('data')
        return self._find_child(profile, 'data', direction=direction)

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
