import logging
import os
from collections import OrderedDict
from xml.etree import ElementTree

import enocean.utils

# Left as a helper
from enocean.protocol.constants import RORG  # noqa: F401


class EEP:
    logger = logging.getLogger('enocean.protocol.eep')

    def __init__(self):
        self.init_ok = False
        self.telegrams = {}

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

    def __load_xml(self):
        self.telegrams = {
            enocean.utils.from_hex_string(telegram.get('rorg')): {
                enocean.utils.from_hex_string(function.get('func')): {
                    enocean.utils.from_hex_string(type.get('type')): type
                    for type in function.iter('profile')
                }
                for function in telegram.iter('profiles')
            }
            for telegram in self.xml_root.iter('telegram')
        }

    @staticmethod
    def _find_child(source, tag, **attributes):
        ''' First child element with the given tag and attribute values (compared as strings), or None. '''
        for child in source.findall(tag):
            if all(child.get(name) == str(value) for name, value in attributes.items()):
                return child
        return None

    @staticmethod
    def _get_raw(source, bitarray):
        ''' Get raw data as integer, based on offset and size '''
        offset = int(source.get('offset'))
        size = int(source.get('size'))
        length = len(bitarray)

        if offset >= length:
            return None

        end = min(length, offset + size)
        return int(''.join(['1' if digit else '0' for digit in bitarray[offset:end]]), 2)

    @staticmethod
    def _set_raw(target, raw_value, bitarray):
        ''' put value into bit array '''
        offset = int(target.get('offset'))
        size = int(target.get('size'))
        for digit in range(size):
            bitarray[offset+digit] = (raw_value >> (size-digit-1)) & 0x01 != 0
        return bitarray

    @staticmethod
    def _get_rangeitem(source, raw_value):
        for rangeitem in source.findall('rangeitem'):
            if raw_value in range(int(rangeitem.get('start', -1)), int(rangeitem.get('end', -1)) + 1):
                return rangeitem

    def _get_value(self, source, bitarray):
        ''' Get value, based on the data in XML '''
        raw_value = self._get_raw(source, bitarray)

        rng = source.find('range')
        rng_min = float(rng.find('min').text)
        rng_max = float(rng.find('max').text)

        scl = source.find('scale')
        scl_min = float(scl.find('min').text)
        scl_max = float(scl.find('max').text)

        return {
            source.get('shortcut'): {
                'description': source.get('description'),
                'unit': source.attrib['unit'],
                'value': (scl_max - scl_min) / (rng_max - rng_min) * (raw_value - rng_min) + scl_min,
                'raw_value': raw_value,
            }
        }

    def _get_enum(self, source, bitarray):
        ''' Get enum value, based on the data in XML '''
        raw_value = self._get_raw(source, bitarray)

        # Find value description.
        value_desc = self._find_child(source, 'item', value=raw_value)
        if value_desc is None:
            value_desc = self._get_rangeitem(source, raw_value)

        return {
            source.get('shortcut'): {
                'description': source.get('description'),
                'unit': source.get('unit', ''),
                'value': (value_desc.get('description').format(value=raw_value)
                          if value_desc is not None and value_desc.get('description') else ''),
                'raw_value': raw_value,
            }
        }

    def _get_boolean(self, source, bitarray):
        ''' Get boolean value, based on the data in XML '''
        raw_value = self._get_raw(source, bitarray)
        return {
            source.get('shortcut'): {
                'description': source.get('description'),
                'unit': source.get('unit', ''),
                'value': True if raw_value else False,
                'raw_value': raw_value,
            }
        }

    def _set_value(self, target, value, bitarray):
        ''' set given numeric value to target field in bitarray '''
        # derive raw value
        rng = target.find('range')
        rng_min = float(rng.find('min').text)
        rng_max = float(rng.find('max').text)
        scl = target.find('scale')
        scl_min = float(scl.find('min').text)
        scl_max = float(scl.find('max').text)
        raw_value = (value - scl_min) * (rng_max - rng_min) / (scl_max - scl_min) + rng_min
        # store value in bitfield
        return self._set_raw(target, int(raw_value), bitarray)

    def _set_enum(self, target, value, bitarray):
        ''' set given enum value (by string or integer value) to target field in bitarray '''
        # derive raw value
        if isinstance(value, int):
            # check whether this value exists
            if self._find_child(target, 'item', value=value) is not None \
                    or self._get_rangeitem(target, value) is not None:
                # set integer values directly
                raw_value = value
            else:
                raise ValueError('Enum value "%s" not found in EEP.' % (value))
        else:
            value_item = self._find_child(target, 'item', description=value)
            if value_item is None:
                raise ValueError('Enum description for value "%s" not found in EEP.' % (value))
            raw_value = int(value_item.get('value'))
        return self._set_raw(target, raw_value, bitarray)

    @staticmethod
    def _set_boolean(target, data, bitarray):
        ''' set given value to target bit in bitarray '''
        bitarray[int(target.get('offset'))] = data
        return bitarray

    def find_profile(self, bitarray, eep_rorg, rorg_func, rorg_type, direction=None, command=None):
        ''' Find profile and data description, matching RORG, FUNC and TYPE '''
        if not self.init_ok:
            self.logger.warning('EEP.xml not loaded!')
            return None

        if eep_rorg not in self.telegrams.keys():
            self.logger.warning('Cannot find rorg %s in EEP!', hex(eep_rorg))
            return None

        if rorg_func not in self.telegrams[eep_rorg].keys():
            self.logger.warning('Cannot find rorg %s func %s in EEP!', hex(eep_rorg), hex(rorg_func))
            return None

        if rorg_type not in self.telegrams[eep_rorg][rorg_func].keys():
            self.logger.warning('Cannot find rorg %s func %s type %s in EEP!',
                             hex(eep_rorg), hex(rorg_func), hex(rorg_type))
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

    def get_values(self, profile, bitarray, status):
        ''' Get keys and values from bitarray '''
        if not self.init_ok or profile is None:
            return [], {}

        output = OrderedDict({})
        for source in profile:
            # Skip fields lying beyond the end of a (truncated) telegram
            if source.tag in ('value', 'enum') and self._get_raw(source, bitarray) is None:
                continue
            if source.tag == 'value':
                output.update(self._get_value(source, bitarray))
            if source.tag == 'enum':
                output.update(self._get_enum(source, bitarray))
            if source.tag == 'status':
                output.update(self._get_boolean(source, status))
        return output.keys(), output

    def set_values(self, profile, data, status, properties):
        ''' Update data based on data contained in properties '''
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
