from enocean import RORG, RadioPacket

# D2-01-12, command 1 (Actuator Set Output): switch output channel 1 on
packet = RadioPacket.create(
    rorg=RORG.VLD,
    rorg_func=0x01,
    rorg_type=0x12,
    command=1,
    destination=[0x05, 0x99, 0x77, 0xAF],
    sender=[0xFF, 0xC3, 0x6F, 0x80],  # the module's base ID
    IO=1,
    OV=100,
)
print(bytes(packet.build()).hex(' '))  # the ESP3 bytes written to the module
print(packet.parsed['OV']['value'])  # Output value 1% to 100% or ON: 100
assert packet.data[1:4] == [0x01, 0x01, 0x64]
