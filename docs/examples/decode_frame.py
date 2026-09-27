from enocean import Packet

# A temperature sensor telegram (A5-02-05) as read from the serial port
frame = bytes.fromhex('55 00 0a 07 01 eb a5 00 00 55 08 01 81 b7 44 00 01 ff ff ff ff 2d 00 75')

status, remaining, packet = Packet.parse_msg(frame)
print(status.name, packet.sender_hex, packet.dbm)  # OK 01:81:B7:44 -45

packet.parse_eep(0x02, 0x05)  # A5-02-05: temperature sensor, 0 °C to +40 °C
temperature = packet.parsed['TMP']
print(temperature['value'], temperature['unit'])  # 26.66... °C
assert round(temperature['value'], 2) == 26.67
