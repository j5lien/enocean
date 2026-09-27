"""Conversions between bytes, integers, bit arrays and hex strings."""

from collections.abc import Iterable


def get_bit(byte: int, bit: int) -> int:
    """Get bit value from byte."""
    return (byte >> bit) & 0x01


def combine_hex(data: Iterable[int]) -> int:
    """Combine list of integer values to one big integer."""
    output = 0x00
    for i, value in enumerate(reversed(list(data))):
        output |= value << i * 8
    return output


def to_bitarray(data: int | list[int] | bytearray, width: int = 8) -> list[bool]:
    """Convert data (list of integers, bytearray or integer) to bitarray."""
    if isinstance(data, (list, bytearray)):
        data = combine_hex(data)
    return [digit == '1' for digit in bin(data)[2:].zfill(width)]


def from_bitarray(data: Iterable[bool]) -> int:
    """Convert bit array back to integer."""
    return int(''.join(['1' if x else '0' for x in data]), 2)


def to_hex_string(data: int | Iterable[int]) -> str:
    """Convert list of integers to a hex string, separated by ":"."""
    if isinstance(data, int):
        return '%02X' % data
    return ':'.join([('%02X' % o) for o in data])


def from_hex_string(hex_string: str) -> int | list[int]:
    """Parse a hex string: '05:99:77:AF' gives [0x05, 0x99, 0x77, 0xAF], a single byte ('A5') an int."""
    reval = [int(x, 16) for x in hex_string.split(':')]
    if len(reval) == 1:
        return reval[0]
    return reval
