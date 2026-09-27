# Profiles

The library supports the 270 profiles of the official EnOcean Alliance specification (EEP 2.6.8), listed in
[SUPPORTED_PROFILES.md](https://github.com/j5lien/enocean/blob/main/SUPPORTED_PROFILES.md). From code:

```python
--8<-- "describe_profile.py"
```

## Fields

- **value** fields map a raw range linearly to a physical scale (e.g. 255..0 → 0..40 °C); `value` is a number.
- **enum** fields map raw values to descriptions; some ranges of raw values carry a scale and decode to a number
  (e.g. D2-05 `POS`: 0..100 %). When building a telegram, give an enum by raw value, by description, or by the label
  before the colon of long descriptions (`R1='Button AI'`).
- **status** fields are bits of the telegram's status byte (e.g. T21, NU of rocker switches).

## Where the profiles come from

`enocean/protocol/profiles/` (one file per profile, loaded on first use) is generated from the official specification
by `tools/generate_eep.py` (`make eep`), plus `tools/eep_additions.xml` for profiles missing from or unusable in the
specification. Some things the specification expresses can't be represented and are reported at generation: values
split over two fields (MSB/LSB) or signed, decoded raw; masked enum values; variants the specification gives no way to
tell apart (D2-30, D2-31 families).
