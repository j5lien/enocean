#!/usr/bin/env python
import codecs

from enocean.protocol.eep import EEP

ROW_FORMAT = '|{:8s}|{:50s}|{:8s}|{:70s}|\n'


eep = EEP()

with codecs.open('SUPPORTED_PROFILES.md', 'w', 'utf-8') as f_handle:
    f_handle.write('# Supported profiles\n')
    f_handle.write('All profiles (should) correspond to the official [EEP](http://www.enocean-alliance.org/eep/) by EnOcean.\n\n')

    for telegram in eep.xml_root.iter('telegram'):
        f_handle.write('### %s (%s)\n' % (telegram.get('description'), telegram.get('rorg')))
        for func in telegram.iter('profiles'):
            # f_handle.write('#####  FUNC %s - %s\n' % (func.get('func'), func.get('description')))
            for profile in func.iter('profile'):
                f_handle.write('##### RORG %s - FUNC %s - TYPE %s - %s\n\n' % (telegram.get('rorg'), func.get('func'), profile.get('type'), profile.get('description')))

                for data in profile.iter('data'):
                    header = []

                    if data.get('direction'):
                        header.append('direction: %s' % (data.get('direction')))
                    if data.get('command'):
                        header.append('command: %s' % (data.get('command')))

                    if header:
                        f_handle.write('###### %s\n' % ' '.join(header))

                    f_handle.write(ROW_FORMAT.format('shortcut', 'description', 'type', 'values'))
                    f_handle.write(ROW_FORMAT.format('--------', '--------------------------------------------------', '--------', '----'))
                    for child in data:
                        values = []
                        for item in child:
                            if item.tag == 'rangeitem':
                                values.append('%s-%s - %s' % (item.get('start'), item.get('end'), item.get('description')))
                            elif item.tag == 'item':
                                values.append('%s - %s' % (item.get('value'), item.get('description')))
                            elif item.tag == 'range':
                                parent = child

                                range_min = float(item.find('min').text)
                                range_max = float(item.find('max').text)
                                scale = parent.find('scale')
                                scale_min = float(scale.find('min').text)
                                scale_max = float(scale.find('max').text)

                                values.append('%s-%s ↔ %s-%s %s' % (range_min, range_max, scale_min, scale_max, parent.get('unit')))
                        if not values:
                            f_handle.write(ROW_FORMAT.format(child.get('shortcut'), child.get('description'), child.tag, ''))
                            continue

                        f_handle.write(ROW_FORMAT.format(child.get('shortcut'), child.get('description'), child.tag, values[0]))
                        for i in range(1, len(values)):
                            f_handle.write(ROW_FORMAT.format('', '', '', values[i]))
                    f_handle.write('\n')
                f_handle.write('\n')

            f_handle.write('\n')
