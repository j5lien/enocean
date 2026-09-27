"""
Data-driven tests over every profile defined in EEP.xml.

- Structural checks: every field fits in the telegram, fields don't overlap, enum values fit in their bits,
  value fields have a usable range, shortcuts are unique.
- Round trip: every enum value and both ends of every value field survive RadioPacket.create() -> parse.
- Snapshot: decoding of fixed bit patterns for every profile is compared to eep_snapshot.json, as a safety net
  when changing how EEP.xml is loaded or interpreted. After an intended change to decoding or to EEP.xml,
  regenerate it with `UPDATE_EEP_SNAPSHOT=1 uv run pytest enocean/protocol/tests/test_eep_profiles.py`
  and review the diff.
"""

import json
import logging
import os
import random

import pytest

from enocean.protocol.constants import RORG
from enocean.protocol.eep import EEP
from enocean.protocol.packet import RadioPacket

logging.getLogger('enocean').setLevel(logging.ERROR)

SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), 'eep_snapshot.json')
CREATABLE_RORGS = (RORG.RPS, RORG.BS1, RORG.BS4, RORG.VLD)
FIXED_WIDTH_BITS = {RORG.RPS: 8, RORG.BS1: 8, RORG.BS4: 32}


class Variant:
    """One <data> block of a profile: what a given telegram (per direction/command) looks like."""

    def __init__(self, rorg, func, type_, profile, data):
        self.rorg, self.func, self.type = rorg, func, type_
        self.data = data
        self.direction = int(data.get('direction')) if data.get('direction') else None
        self.command = int(data.get('command')) if data.get('command') else None
        command_tag = profile.find('command')
        self.command_shortcut = command_tag.get('shortcut') if command_tag is not None else None
        self.id = '%02X-%02X-%02X' % (rorg, func, type_)
        if self.direction is not None:
            self.id += '-dir%d' % self.direction
        if self.command is not None:
            self.id += '-cmd%d' % self.command

    @property
    def fields(self):
        return [tag for tag in self.data if tag.tag in ('value', 'enum', 'status')]

    @property
    def data_fields(self):
        return [tag for tag in self.fields if tag.tag != 'status']

    @property
    def width(self):
        if self.rorg == RORG.VLD:
            return int(self.data.get('bits')) * 8 if self.data.get('bits') else None
        return FIXED_WIDTH_BITS.get(self.rorg)

    def is_command_field(self, tag):
        return tag.get('shortcut') in ('CMD', self.command_shortcut)

    def packet(self, payload, status=0):
        data = [self.rorg] + list(payload) + [0x01, 0x02, 0x03, 0x04, status]
        packet = RadioPacket(1, data, [0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0x40, 0x00])
        packet.parse_eep(self.func, self.type, self.direction, self.command)
        return packet


def load_variants():
    eep = EEP()
    return [
        Variant(rorg, func, type_, profile, data)
        for rorg, funcs in sorted(eep.telegrams.items())
        for func, types in sorted(funcs.items())
        for type_, profile in sorted(types.items())
        for data in profile.findall('data')
    ]


VARIANTS = load_variants()
CREATABLE = [v for v in VARIANTS if v.rorg in CREATABLE_RORGS]


def by_id(variants):
    return pytest.mark.parametrize('variant', variants, ids=[v.id for v in variants])


def bits(tag):
    return range(int(tag.get('offset')), int(tag.get('offset')) + int(tag.get('size')))


def enum_values(tag):
    values = [int(item.get('value')) for item in tag.findall('item')]
    for rangeitem in tag.findall('rangeitem'):
        values += [int(rangeitem.get('start')), int(rangeitem.get('end'))]
    return sorted(set(values))


def range_and_scale(tag):
    rng, scl = tag.find('range'), tag.find('scale')
    return (
        float(rng.find('min').text),
        float(rng.find('max').text),
        float(scl.find('min').text),
        float(scl.find('max').text),
    )


# --- Structural checks ---------------------------------------------------------------------------------------------


def test_every_profile_is_covered():
    assert len({(v.rorg, v.func, v.type) for v in VARIANTS}) == sum(
        len(types) for funcs in EEP().telegrams.values() for types in funcs.values()
    )


@by_id(VARIANTS)
def test_fields_fit_in_telegram(variant):
    if variant.rorg == RORG.VLD:
        assert variant.width, 'VLD <data> must declare its length in bytes ("bits" attribute)'
    for tag in variant.data_fields:
        assert max(bits(tag)) < variant.width, '%s (bits %d..%d) exceeds %d bits' % (
            tag.get('shortcut'),
            min(bits(tag)),
            max(bits(tag)),
            variant.width,
        )
    for tag in variant.fields:
        if tag.tag == 'status':
            assert 0 <= int(tag.get('offset')) < 8 and int(tag.get('size')) == 1, tag.get('shortcut')


@by_id(VARIANTS)
def test_fields_do_not_overlap(variant):
    owner = {}
    for tag in variant.data_fields:
        for bit in bits(tag):
            assert bit not in owner, '%s overlaps %s at bit %d' % (tag.get('shortcut'), owner[bit], bit)
            owner[bit] = tag.get('shortcut')


@by_id(VARIANTS)
def test_shortcuts_are_unique(variant):
    shortcuts = [tag.get('shortcut') for tag in variant.fields]
    assert len(shortcuts) == len(set(shortcuts))


@by_id(VARIANTS)
def test_enum_values_fit_in_field(variant):
    for tag in variant.data_fields:
        if tag.tag == 'enum':
            too_big = [value for value in enum_values(tag) if value >= 2 ** int(tag.get('size'))]
            assert not too_big, '%s: values %s do not fit in %s bits' % (tag.get('shortcut'), too_big, tag.get('size'))


@by_id(VARIANTS)
def test_value_fields_have_usable_range(variant):
    for tag in variant.data_fields:
        if tag.tag == 'value':
            rng_min, rng_max, scl_min, scl_max = range_and_scale(tag)
            assert rng_min != rng_max and scl_min != scl_max, tag.get('shortcut')
            assert 0 <= min(rng_min, rng_max) and max(rng_min, rng_max) < 2 ** int(tag.get('size')), (
                '%s: range %g..%g does not fit in %s bits' % (tag.get('shortcut'), rng_min, rng_max, tag.get('size'))
            )


@by_id(VARIANTS)
def test_truncated_telegram_decodes_fields_present(variant):
    variant.packet([0x00])  # must not raise, whatever the profile length


# --- Round trip ----------------------------------------------------------------------------------------------------


def create(variant, learn=False, **values):
    return RadioPacket.create(
        rorg=variant.rorg,
        rorg_func=variant.func,
        rorg_type=variant.type,
        direction=variant.direction,
        command=variant.command,
        sender=[0x01, 0x02, 0x03, 0x04],
        learn=learn,
        **values,
    )


@by_id(CREATABLE)
def test_create_default_packet(variant):
    packet = create(variant)
    assert packet.rorg == variant.rorg
    if variant.width:
        assert len(packet.data) == 1 + variant.width // 8 + 5


@by_id(CREATABLE)
def test_enum_values_round_trip(variant):
    for tag in variant.data_fields:
        if tag.tag != 'enum' or variant.is_command_field(tag):
            continue
        for value in enum_values(tag):
            if tag.get('shortcut') == 'LRNB':
                # The 4BS learn bit is driven by create(learn=...), not by the field value
                packet = create(variant, learn=(value == 0))
            else:
                packet = create(variant, **{tag.get('shortcut'): value})
            assert packet.parsed[tag.get('shortcut')]['raw_value'] == value, '%s=%d' % (tag.get('shortcut'), value)


@by_id(CREATABLE)
def test_value_fields_round_trip(variant):
    for tag in variant.data_fields:
        if tag.tag != 'value':
            continue
        rng_min, rng_max, scl_min, scl_max = range_and_scale(tag)
        for scaled, raw in ((scl_min, rng_min), (scl_max, rng_max)):
            packet = create(variant, **{tag.get('shortcut'): scaled})
            parsed = packet.parsed[tag.get('shortcut')]
            assert parsed['raw_value'] == raw, '%s=%g' % (tag.get('shortcut'), scaled)
            assert parsed['value'] == pytest.approx(scaled), tag.get('shortcut')


@by_id([v for v in CREATABLE if any(tag.tag == 'status' for tag in v.fields)])
def test_status_fields_round_trip(variant):
    for tag in variant.fields:
        if tag.tag == 'status':
            for value in (True, False):
                packet = create(variant, **{tag.get('shortcut'): value})
                assert packet.parsed[tag.get('shortcut')]['value'] is value, '%s=%s' % (tag.get('shortcut'), value)


# --- Snapshot ------------------------------------------------------------------------------------------------------


def patterns(variant):
    size = (variant.width or 8) // 8
    rnd = random.Random(variant.id)
    return {
        'zeros': ([0x00] * size, 0x00),
        'ones': ([0xFF] * size, 0xFF),
        'alternating': ([0xA5, 0x5A] * size)[:size],
        'random1': [rnd.randint(0, 255) for _ in range(size)],
        'random2': [rnd.randint(0, 255) for _ in range(size)],
    }


def decode_all(variant):
    decoded = {}
    for name, pattern in patterns(variant).items():
        payload, status = pattern if isinstance(pattern, tuple) else (pattern, 0x30)
        parsed = variant.packet(payload, status).parsed
        decoded[name] = {
            shortcut: [round(v['value'], 6) if isinstance(v['value'], float) else v['value'], v['raw_value']]
            for shortcut, v in parsed.items()
        }
    return decoded


def test_decoding_matches_snapshot():
    current = {variant.id: decode_all(variant) for variant in VARIANTS}
    if os.environ.get('UPDATE_EEP_SNAPSHOT') == '1':
        with open(SNAPSHOT_PATH, 'w', encoding='utf-8') as snapshot:
            json.dump(current, snapshot, indent=1, sort_keys=True, ensure_ascii=False)
            snapshot.write('\n')
    with open(SNAPSHOT_PATH, encoding='utf-8') as snapshot:
        expected = json.load(snapshot)

    assert sorted(current) == sorted(expected), 'profiles added or removed: regenerate the snapshot'
    for variant_id in sorted(expected):
        assert current[variant_id] == expected[variant_id], variant_id
