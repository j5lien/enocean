from enocean import EEP

eep = EEP()
print(len(list(eep.profiles())), 'profiles')

for variant in eep.describe('D2-01-12'):
    print('command', variant.command, [field.shortcut for field in variant.fields])

output_value = next(variant for variant in eep.describe('D2-01-12') if variant.command == 1).field('OV')
print(output_value.kind, output_value.offset, output_value.size)  # enum 17 7
print(output_value.items[0], output_value.ranges[0])
assert output_value.items[0] == 'Output value 0% or OFF'
