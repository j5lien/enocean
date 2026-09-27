#!/usr/bin/env python
"""
Generates enocean/protocol/EEP.xml from the official EnOcean Alliance specification (EEP 2.6.8 XML).

    uv run python tools/generate_eep.py        # or: make eep

The specification is downloaded into .cache/ (not versioned: only the derived file is published) and checked
against a known SHA-256. It is converted to the library's compact format:

- <ref> types (e.g. D2-01-12, which shares the D2-01 message table) are resolved;
- each <case> becomes a <data> variant, its <condition> becoming <condition> elements (data or status bits the
  telegram must carry), plus `command` / `direction` attributes and a profile-level <command> when the variants are
  told apart by a command field;
- data fields become <value> (linear raw range -> scale) or <enum> (items, and ranges that may be scaled), status
  fields <status>; reserved fields are dropped;
- shortcuts are made valid Python identifiers (I/O -> IO) and deduplicated.

Profiles in tools/eep_additions.xml then replace or complete the official ones.
"""

import hashlib
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import quoteattr

ROOT = Path(__file__).resolve().parent.parent
SPEC_URL = 'https://tools.enocean-alliance.org/EEPViewer/profiles/eep268.xml'
SPEC_SHA256 = 'c0ff5ebec06bdf3d7e9a251774d1ac6de5f895eb625ac5aacc3e9634aa23c426'
SPEC_VERSION = '2.6.8'
CACHE = ROOT / '.cache' / 'eep268.xml'
ADDITIONS = ROOT / 'tools' / 'eep_additions.xml'
OUTPUT = ROOT / 'enocean' / 'protocol' / 'EEP.xml'

TELEGRAM_TYPES = {0xF6: 'RPS', 0xD5: '1BS', 0xA5: '4BS', 0xD2: 'VLD'}
# Payload length in bits of telegrams whose length doesn't depend on the profile
FIXED_LENGTH = {0xF6: 8, 0xD5: 8, 0xA5: 32}

warnings: list[str] = []


def download() -> Path:
    if not CACHE.exists():
        CACHE.parent.mkdir(exist_ok=True)
        print('Downloading %s' % SPEC_URL, file=sys.stderr)
        try:
            with urllib.request.urlopen(SPEC_URL) as response:  # noqa: S310 - fixed https URL
                CACHE.write_bytes(response.read())
        except urllib.error.URLError:
            # e.g. a python.org macOS Python without root certificates: curl uses the system's
            subprocess.run(['curl', '-fsSL', '-o', str(CACHE), SPEC_URL], check=True)
    digest = hashlib.sha256(CACHE.read_bytes()).hexdigest()
    if digest != SPEC_SHA256:
        sys.exit(
            '%s has SHA-256 %s, expected %s: new specification? Review it and update SPEC_SHA256.'
            % (CACHE, digest, SPEC_SHA256)
        )
    return CACHE


def load(path: Path) -> ET.Element:
    source = re.sub(r'<!DOCTYPE[^>]*>', '', path.read_bytes().decode('utf-16'))
    return ET.fromstring(source.replace('encoding="utf-16le"', ''))


def text(element: ET.Element | None, path: str = '.') -> str:
    found = element.find(path) if element is not None else None
    return ' '.join(''.join(found.itertext()).split()) if found is not None else ''


def number(value: str) -> float:
    value = value.strip().replace(',', '.')
    try:
        return int(value, 0)
    except ValueError:
        return float(value)


def integer(value: str) -> int:
    return int(value.strip(), 0)


def maybe_integer(value: str | None) -> int | None:
    try:
        return integer(value or '')
    except ValueError:
        return None


def pair(field: ET.Element, tag: str) -> tuple[float, float] | None:
    """(min, max) of a <range> or <scale>, None if missing or not numeric."""
    try:
        return number(field.findtext(tag + '/min') or ''), number(field.findtext(tag + '/max') or '')
    except ValueError:
        return None


def fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def escape_format(description: str) -> str:
    """Descriptions go through str.format(value=raw): keep literal braces literal."""
    return description.replace('{', '{{').replace('}', '}}')


def identifier(shortcut: str) -> str:
    return re.sub(r'[^0-9A-Za-z_]', '', shortcut)


class Spec:
    def __init__(self, root: ET.Element) -> None:
        self.types: dict[tuple[int, int, int], ET.Element] = {}
        for rorg in root.find('profile').findall('rorg'):
            for func in rorg.findall('func'):
                for type_ in func.findall('type'):
                    key = (
                        integer(rorg.findtext('number')),
                        integer(func.findtext('number')),
                        integer(type_.findtext('number')),
                    )
                    self.types[key] = type_
        self.root = root

    def resolve(self, type_: ET.Element) -> ET.Element:
        seen = set()
        while type_.find('ref') is not None:
            ref = type_.find('ref')
            key = (int(ref.findtext('rorg'), 16), int(ref.findtext('func'), 16), int(ref.findtext('type'), 16))
            if key in seen or key not in self.types:
                raise ValueError('Unresolvable <ref> to %02X-%02X-%02X' % key)
            seen.add(key)
            type_ = self.types[key]
        return type_


def data_fields(case: ET.Element) -> list[ET.Element]:
    return [field for field in case.findall('datafield') if field.find('reserved') is None]


def single_value(field: ET.Element) -> int | None:
    """The value of an enum field that can only hold one (e.g. CMD in each D2-01 case)."""
    enum = field.find('enum')
    if enum is None:
        return None
    items = enum.findall('item')
    if len(items) != 1:
        return None
    return maybe_integer(items[0].findtext('value'))


def conditions(case: ET.Element) -> list[tuple[str, int, int, int]]:
    """(source, offset, size, value) the telegram must match for this case, from its <condition>."""
    condition = case.find('condition')
    result = []
    if condition is not None:
        for part in condition:
            if part.tag in ('datafield', 'statusfield'):
                source = 'data' if part.tag == 'datafield' else 'status'
                values = [maybe_integer(part.findtext(tag)) for tag in ('bitoffs', 'bitsize', 'value')]
                if None in values:
                    warnings.append(
                        'condition %r not representable, dropped' % ET.tostring(part, encoding='unicode')[:80]
                    )
                    continue
                result.append((source, *values))
    return result


def infer_conditions(cases: list[ET.Element]) -> list[list[tuple[str, int, int, int]]]:
    """
    Conditions of every case. Cases without an explicit one are told apart by the fields they fix to a single value
    (e.g. D2-01: CMD, plus ECID for extended commands), or else by the item of a shared enum their title names
    (e.g. D2-50: "Ventilation Basic Status" is message type MT = 2).
    """
    explicit = [conditions(case) for case in cases]
    if len(cases) < 2 or any(direction(case) is not None for case in cases):
        return explicit
    # Fields fixed to a single value in at least two cases, with different values: they tell the cases apart
    # (not mere flags documented with a single value, e.g. A5-20-01 "true")
    singles: dict[tuple[int, int], set[int]] = {}
    counts: Counter = Counter()
    for case in cases:
        for field in data_fields(case):
            value = single_value(field)
            if value is not None:
                position = (integer(field.findtext('bitoffs')), integer(field.findtext('bitsize')))
                singles.setdefault(position, set()).add(value)
                counts[position] += 1
    discriminating = {position for position, values in singles.items() if counts[position] >= 2 and len(values) >= 2}
    result = []
    for case, found in zip(cases, explicit, strict=True):
        if not found:
            for field in data_fields(case):
                value = single_value(field)
                position = (integer(field.findtext('bitoffs')), integer(field.findtext('bitsize')))
                if value is not None and position in discriminating:
                    found.append(('data', *position, value))
        result.append(found)
    if any(not found for found in result):
        by_title = conditions_from_titles(cases)
        if by_title:
            result = [found or by_title[index] for index, found in enumerate(result)]
    return result


def conditions_from_titles(cases: list[ET.Element]) -> list[list[tuple[str, int, int, int]]] | None:
    first = cases[0]
    for field in data_fields(first):
        enum = field.find('enum')
        position = (field.findtext('bitoffs'), field.findtext('bitsize'))
        if enum is None or not all(
            any((f.findtext('bitoffs'), f.findtext('bitsize')) == position for f in data_fields(case)) for case in cases
        ):
            continue
        items = [
            (maybe_integer(item.findtext('value')), text(item, 'description').lower()) for item in enum.findall('item')
        ]
        matched = []
        for case in cases:
            title = text(case, 'title').lower()
            values = [
                value for value, description in items if value is not None and description and description in title
            ]
            if len(values) != 1:
                break
            matched.append([('data', integer(position[0]), integer(position[1]), values[0])])
        else:
            if len({found[0][3] for found in matched}) == len(cases):
                return matched
    return None


def direction(case: ET.Element) -> int | None:
    condition = case.find('condition')
    value = condition.findtext('direction') if condition is not None else None
    return integer(value) if value else None


def payload_bits(rorg: int, case: ET.Element) -> int:
    if rorg in FIXED_LENGTH:
        return FIXED_LENGTH[rorg]
    ends = [integer(f.findtext('bitoffs')) + integer(f.findtext('bitsize')) for f in case.findall('datafield')]
    return max(ends, default=8)


def convert_enum_item(item: ET.Element, pid: str, shortcut: str, size: int) -> str:
    try:
        line = _convert_enum_item(item)
        values = [int(v) for v in re.findall(r'(?:value|start|end)="(\d+)"', line)]
        if values and max(values) > 2**size - 1:
            warnings.append('%s %s: enum item %s does not fit in %d bits, dropped' % (pid, shortcut, max(values), size))
            return ''
        return line
    except ValueError:
        # e.g. 0b11X0XXXX: values with don't-care bits can't be expressed
        warnings.append('%s %s: enum item %r not representable, dropped' % (pid, shortcut, text(item, 'value')))
        return ''


def _convert_enum_item(item: ET.Element) -> str:
    description = escape_format(text(item, 'description'))
    value = text(item, 'value')
    # Ranges also appear written in <value> ("34 ... 35"), and values annotated ("32767 (0x7FFF)")
    written_range = re.match(r'^(\S+)\s*(?:\.\.\.|…)\s*(\S+)', value)
    if item.find('min') is None and written_range:
        start, end = (integer(bound) for bound in written_range.groups())
        return '<rangeitem start="%d" end="%d" description=%s />' % (start, end, quoteattr(description + ': {value}'))
    if item.find('min') is None and value:
        value = value.split()[0]
    if item.find('min') is not None:
        start, end = integer(item.findtext('min')), integer(item.findtext('max'))
        attributes = 'start="%d" end="%d"' % (start, end)
        scale = item.find('scale')
        if scale is not None and scale.find('min') is not None:
            attributes += ' scale-min="%s" scale-max="%s"' % (
                fmt(number(scale.findtext('min'))),
                fmt(number(scale.findtext('max'))),
            )
            if text(item, 'unit'):
                attributes += ' unit=%s' % quoteattr(text(item, 'unit'))
        elif start != end:
            # Keep the raw value visible for ranges: "Output channel (to load): 3"
            description += ': {value}'
        return '<rangeitem %s description=%s />' % (attributes, quoteattr(description))
    if value:
        return '<item value="%d" description=%s />' % (integer(value), quoteattr(description))
    return ''


def convert_field(field: ET.Element, shortcut: str, pid: str) -> str:
    offset, size = integer(field.findtext('bitoffs')), integer(field.findtext('bitsize'))
    attributes = 'description=%s shortcut=%s offset="%d" size="%d"' % (
        quoteattr(text(field, 'data')),
        quoteattr(shortcut),
        offset,
        size,
    )
    unit = text(field, 'unit')
    enum = field.find('enum')
    if enum is not None:
        items = [
            line for line in (convert_enum_item(item, pid, shortcut, size) for item in enum.findall('item')) if line
        ]
        if unit:
            attributes += ' unit=%s' % quoteattr(unit)
        return '<enum %s>\n%s\n</enum>' % (attributes, '\n'.join(items))
    raw = pair(field, 'range')
    scale = pair(field, 'scale') or raw
    if raw is None or min(raw) < 0 or max(raw) > 2**size - 1:
        # Missing range, signed values, or a value split across MSB/LSB fields that each carry the full range
        warnings.append(
            '%s %s: range %s not representable in %d bits, decoded as a raw number' % (pid, shortcut, raw, size)
        )
        raw = scale = (0, 2**size - 1)
    return (
        '<value %s unit=%s>\n' % (attributes, quoteattr(unit))
        + '<range><min>%s</min><max>%s</max></range>\n' % (fmt(raw[0]), fmt(raw[1]))
        + '<scale><min>%s</min><max>%s</max></scale>\n</value>' % (fmt(scale[0]), fmt(scale[1]))
    )


def field_at(case: ET.Element, offset: int, size: int) -> ET.Element | None:
    return next(
        (
            f
            for f in data_fields(case)
            if (integer(f.findtext('bitoffs')), integer(f.findtext('bitsize'))) == (offset, size)
        ),
        None,
    )


def condition_shortcuts(case: ET.Element, case_conditions: list) -> dict[str, int]:
    """Shortcut -> required value, for the data fields a case's conditions are about."""
    result = {}
    for source, offset, size, value in case_conditions:
        field = field_at(case, offset, size) if source == 'data' else None
        if field is not None:
            result[identifier(text(field, 'shortcut'))] = value
    return result


def convert_case(rorg: int, case: ET.Element, case_conditions: list, command_shortcut: str | None, pid: str) -> str:
    attributes = []
    case_direction = direction(case)
    if case_direction is not None:
        attributes.append('direction="%d"' % case_direction)
    required = condition_shortcuts(case, case_conditions)
    if command_shortcut is not None and command_shortcut in required:
        attributes.append('command="%d"' % required[command_shortcut])
    if rorg == 0xD2:
        attributes.append('bits="%d"' % ((payload_bits(rorg, case) + 7) // 8))
    lines = ['<condition source="%s" offset="%d" size="%d" value="%d" />' % c for c in case_conditions]
    used = Counter()
    for field in data_fields(case):
        name = identifier(text(field, 'shortcut'))
        if not name:
            warnings.append('%s: field %r without shortcut, dropped' % (pid, text(field, 'data')))
            continue
        used[name] += 1
        if used[name] > 1:
            warnings.append('%s: duplicate shortcut %s renamed %s_%d' % (pid, name, name, used[name]))
            name = '%s_%d' % (name, used[name])
        converted = convert_field(field, name, pid)
        if name in required and converted.startswith('<enum') and 'value="%d"' % required[name] not in converted:
            # The spec's own condition value missing from the field's items (e.g. D2-11 MID): name it after the case
            item = '<item value="%d" description=%s />' % (
                required[name],
                quoteattr(escape_format(text(case, 'title'))),
            )
            converted = converted.replace('\n</enum>', '\n%s\n</enum>' % item)
        lines.append(converted)
    for field in case.findall('statusfield'):
        name = identifier(text(field, 'data'))
        if name and field.find('bitoffs') is not None:
            lines.append(
                '<status description=%s shortcut=%s offset="%d" size="%d" />'
                % (
                    quoteattr(text(field, 'data')),
                    quoteattr(name),
                    integer(field.findtext('bitoffs')),
                    integer(field.findtext('bitsize')),
                )
            )
    return '<data%s>\n%s\n</data>' % (''.join(' ' + a for a in attributes), '\n'.join(lines))


def convert_type(rorg: int, spec: Spec, type_: ET.Element, function_title: str, pid: str) -> str | None:
    definition = spec.resolve(type_)
    cases = definition.findall('case')
    if not cases:
        warnings.append('%s: no definition in the specification, skipped' % pid)
        return None
    all_conditions = infer_conditions(cases)
    # Variants all conditioned on a field of the same name (e.g. CMD, wherever it sits) are told apart by a command:
    # profile-level <command>, `command` attributes
    command_shortcut = None
    command_line = ''
    if len(cases) > 1 and all(all_conditions):
        named = [condition_shortcuts(case, conds) for case, conds in zip(cases, all_conditions, strict=True)]
        shared = set.intersection(*(set(names) for names in named))
        if shared:
            command_shortcut = next((name for name in ('CMD', 'COM', 'MID', 'MT') if name in shared), sorted(shared)[0])
            first = next(
                c
                for c in all_conditions[0]
                if c[0] == 'data'
                and field_at(cases[0], c[1], c[2]) is not None
                and identifier(text(field_at(cases[0], c[1], c[2]), 'shortcut')) == command_shortcut
            )
            command_line = '<command description="Command identifier" shortcut=%s offset="%d" size="%d" />\n' % (
                quoteattr(command_shortcut),
                first[1],
                first[2],
            )
    signatures = [tuple(sorted(conds)) for conds in all_conditions]
    for index, signature in enumerate(signatures):
        if signature and signature in signatures[:index]:
            warnings.append(
                '%s: variant %d has the same conditions as an earlier one: never detected automatically'
                % (pid, index + 1)
            )
    body = '\n'.join(
        convert_case(rorg, case, conds, command_shortcut, pid)
        for case, conds in zip(cases, all_conditions, strict=True)
    )
    title = text(type_, 'title')
    if title.startswith('Type 0x'):
        # Generic titles ("Type 0x12 (description: see table)"): name the type after its family
        title = '%s - Type 0x%02X' % (function_title, integer(type_.findtext('number')))
    return '<profile type="0x%02X" description=%s>\n%s%s\n</profile>' % (
        integer(type_.findtext('number')),
        quoteattr(title),
        command_line,
        body,
    )


def generate(spec: Spec) -> str:
    additions = ET.parse(ADDITIONS).getroot()
    replaced = {
        (int(telegram.get('rorg'), 16), int(func.get('func'), 16), int(profile.get('type'), 16))
        for telegram in additions.iter('telegram')
        for func in telegram.iter('profiles')
        for profile in func.iter('profile')
    }
    telegrams: dict[int, tuple[str, dict[int, tuple[str, dict[int, str]]]]] = {}
    for rorg_element in spec.root.find('profile').findall('rorg'):
        rorg = integer(rorg_element.findtext('number'))
        functions = telegrams.setdefault(rorg, (text(rorg_element, 'title'), {}))[1]
        for func_element in rorg_element.findall('func'):
            func = integer(func_element.findtext('number'))
            profiles = functions.setdefault(func, (text(func_element, 'title'), {}))[1]
            for type_element in func_element.findall('type'):
                type_ = integer(type_element.findtext('number'))
                pid = '%02X-%02X-%02X' % (rorg, func, type_)
                if (rorg, func, type_) in replaced:
                    continue
                converted = convert_type(rorg, spec, type_element, text(func_element, 'title'), pid)
                if converted:
                    profiles[type_] = converted

    for telegram in additions.iter('telegram'):
        rorg = int(telegram.get('rorg'), 16)
        functions = telegrams.setdefault(rorg, (telegram.get('description', ''), {}))[1]
        for func_element in telegram.iter('profiles'):
            func = int(func_element.get('func'), 16)
            profiles = functions.setdefault(func, (func_element.get('description', ''), {}))[1]
            for profile in func_element.iter('profile'):
                profiles[int(profile.get('type'), 16)] = ET.tostring(profile, encoding='unicode').strip()

    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!-- Generated by tools/generate_eep.py from the EnOcean Alliance EEP %s specification (%s) and'
        % (SPEC_VERSION, SPEC_URL),
        '     tools/eep_additions.xml. Do not edit: change the generator or the additions and regenerate. -->',
        '<telegrams version="%s">' % SPEC_VERSION,
    ]
    for rorg, (rorg_title, functions) in sorted(telegrams.items()):
        out.append(
            '<telegram rorg="0x%02X" type=%s description=%s>'
            % (rorg, quoteattr(TELEGRAM_TYPES.get(rorg, '')), quoteattr(rorg_title))
        )
        for func, (func_title, profiles) in sorted(functions.items()):
            if profiles:
                out.append('<profiles func="0x%02X" description=%s>' % (func, quoteattr(func_title)))
                out.extend(profile for _, profile in sorted(profiles.items()))
                out.append('</profiles>')
        out.append('</telegram>')
    out.append('</telegrams>')
    tree = ET.ElementTree(ET.fromstring('\n'.join(out[3:])))
    ET.indent(tree, space='  ')
    return '\n'.join(out[:3]) + '\n' + ET.tostring(tree.getroot(), encoding='unicode') + '\n'


def main() -> None:
    spec = Spec(load(download()))
    OUTPUT.write_text(generate(spec), encoding='utf-8')
    count = len(ET.parse(OUTPUT).getroot().findall('.//profile'))
    print('Wrote %s: %d profiles' % (OUTPUT.relative_to(ROOT), count), file=sys.stderr)
    for warning in warnings:
        print('  warning: %s' % warning, file=sys.stderr)


if __name__ == '__main__':
    main()
