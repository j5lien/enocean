import json

from enocean import RORG, DeviceRegistry, Packet

devices = DeviceRegistry.from_config(
    {
        '00:37:7E:06': {'eep': 'F6-02-02', 'name': 'Office wall switch', 'room': 'office'},
        '05:99:77:AF': {'eep': 'D2-01-12', 'name': 'Office light'},
    },
    defaults={RORG.RPS: 'F6-02-02'},  # profile to try for unknown devices, by RORG
    ignored=['FF:E8:06:02'],  # dropped by communicators using this registry
)

# The office light reporting channel 1 on (D2-01-12, command 4)
_, _, packet = Packet.parse_msg(bytes.fromhex('55 00 09 07 01 56 d2 04 61 e4 05 99 77 af 00 01 ff ff ff ff 49 00 93'))
device = devices.decode(packet)  # communicators given devices= do this for you

print(device.name, packet.eep_id, packet.command)  # Office light D2-01-12 4
print(packet.parsed['OV']['value'])  # Output value 1% to 100% or ON: 100
print(json.dumps(packet.to_dict(), indent=2))  # e.g. to index or publish it
assert packet.parsed['IO']['raw_value'] == 1
