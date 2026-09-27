# Supported profiles
All profiles (should) correspond to the official [EEP](http://www.enocean-alliance.org/eep/) by EnOcean.

### RPS Telegram (0xF6)
##### RORG 0xF6 - FUNC 0x01 - TYPE 0x01 - Push Button

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|PB      |Status of the push button                         |enum    |0 - Released                                                          |
|        |                                                  |        |1 - Pressed                                                           |



##### RORG 0xF6 - FUNC 0x02 - TYPE 0x01 - Light and Blind Control - Application Style 1

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|R1      |Rocker 1st action                                 |enum    |0 - Button AI                                                         |
|        |                                                  |        |1 - Button AO                                                         |
|        |                                                  |        |2 - Button BI                                                         |
|        |                                                  |        |3 - Button BO                                                         |
|EB      |Energy bow                                        |enum    |0 - released                                                          |
|        |                                                  |        |1 - pressed                                                           |
|R2      |Rocker 2nd action                                 |enum    |0 - Button AI                                                         |
|        |                                                  |        |1 - Button AO                                                         |
|        |                                                  |        |2 - Button BI                                                         |
|        |                                                  |        |3 - Button BO                                                         |
|SA      |2nd action                                        |enum    |0 - No 2nd action                                                     |
|        |                                                  |        |1 - 2nd action valid                                                  |
|T21     |T21                                               |status  |                                                                      |
|NU      |NU                                                |status  |                                                                      |


##### RORG 0xF6 - FUNC 0x02 - TYPE 0x02 - Light and Blind Control - Application Style 2

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|R1      |Rocker 1st action                                 |enum    |0 - Button AI                                                         |
|        |                                                  |        |1 - Button AO                                                         |
|        |                                                  |        |2 - Button BI                                                         |
|        |                                                  |        |3 - Button BO                                                         |
|EB      |Energy bow                                        |enum    |0 - released                                                          |
|        |                                                  |        |1 - pressed                                                           |
|R2      |Rocker 2nd action                                 |enum    |0 - Button AI                                                         |
|        |                                                  |        |1 - Button AO                                                         |
|        |                                                  |        |2 - Button BI                                                         |
|        |                                                  |        |3 - Button BO                                                         |
|SA      |2nd action                                        |enum    |0 - No 2nd action                                                     |
|        |                                                  |        |1 - 2nd action valid                                                  |
|T21     |T21                                               |status  |                                                                      |
|NU      |NU                                                |status  |                                                                      |


##### RORG 0xF6 - FUNC 0x02 - TYPE 0x03 - Light Control - Application Style 1

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|RA      |Rocker action                                     |enum    |48 - Button AO                                                        |
|        |                                                  |        |16 - Button AI                                                        |
|        |                                                  |        |112 - Button BO                                                       |
|        |                                                  |        |80 - Button BI                                                        |
|T21     |T21                                               |status  |                                                                      |
|NU      |NU                                                |status  |                                                                      |


##### RORG 0xF6 - FUNC 0x02 - TYPE 0x04 - Light and blind control ERP2

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|EB      |State of the energy bow                           |enum    |0 - released                                                          |
|        |                                                  |        |1 - pressed                                                           |
|BC      |Button coding                                     |enum    |0 - button                                                            |
|RBI     |State I of the rocker B                           |enum    |0 - not pressed                                                       |
|        |                                                  |        |1 - pressed                                                           |
|RBO     |State O of the rocker B                           |enum    |0 - not pressed                                                       |
|        |                                                  |        |1 - pressed                                                           |
|RAI     |State I of the rocker A                           |enum    |0 - not pressed                                                       |
|        |                                                  |        |1 - pressed                                                           |
|RAO     |State O of the rocker A                           |enum    |0 - not pressed                                                       |
|        |                                                  |        |1 - pressed                                                           |



##### RORG 0xF6 - FUNC 0x05 - TYPE 0x01 - Liquid Leakage Sensor (mechanic harvester)

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|WAS     |Water Sensor                                      |enum    |0-16 - not specified                                                  |
|        |                                                  |        |17 - Water detected                                                   |
|        |                                                  |        |18-255 - not specified                                                |
|T21     |T21                                               |status  |                                                                      |
|NU      |NU                                                |status  |                                                                      |


##### RORG 0xF6 - FUNC 0x05 - TYPE 0x02 - Smoke Detector

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SMO     |Status of detection and battery                   |enum    |0 - Smoke Alarm OFF                                                   |
|        |                                                  |        |16 - Smoke Alarm ON                                                   |
|        |                                                  |        |48 - Energy LOW                                                       |



##### RORG 0xF6 - FUNC 0x10 - TYPE 0x00 - Window Handle

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|WIN     |Window handle                                     |enum    |0 - Moved from up to vertical                                         |
|        |                                                  |        |1 - Moved from vertical to up                                         |
|        |                                                  |        |2 - Moved from down to vertical                                       |
|        |                                                  |        |3 - Moved from vertical to down                                       |
|T21     |T21                                               |status  |                                                                      |
|NU      |NU                                                |status  |                                                                      |



### 1BS Telegram (0xD5)
##### RORG 0xD5 - FUNC 0x00 - TYPE 0x01 - Single Input Contact

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CO      |Contact                                           |enum    |0 - open                                                              |
|        |                                                  |        |1 - closed                                                            |



### 4BS Telegram (0xA5)
##### RORG 0xA5 - FUNC 0x02 - TYPE 0x01 - Temperature Sensor Range -40°C to 0°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -40.0-0.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x02 - Temperature Sensor Range -30°C to +10°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -30.0-10.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x03 - Temperature Sensor Range -20°C to +20°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -20.0-20.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x04 - Temperature Sensor Range -10°C to +30°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -10.0-30.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x05 - Temperature Sensor Range 0°C to +40°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 0.0-40.0 °C                                               |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x06 - Temperature Sensor Range +10°C to +50°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 10.0-50.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x07 - Temperature Sensor Range +20°C to +60°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 20.0-60.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x08 - Temperature Sensor Range +30°C to +70°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 30.0-70.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x09 - Temperature Sensor Range +40°C to +80°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 40.0-80.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x0A - Temperature Sensor Range +50°C to +90°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 50.0-90.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x0B - Temperature Sensor Range +60°C to +100°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 60.0-100.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x10 - Temperature Sensor Range -60°C to +20°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -60.0-20.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x11 - Temperature Sensor Range -50°C to +30°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -50.0-30.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x12 - Temperature Sensor Range -40°C to +40°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -40.0-40.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x13 - Temperature Sensor Range -30°C to +50°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -30.0-50.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x14 - Temperature Sensor Range -20°C to +60°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -20.0-60.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x15 - Temperature Sensor Range -10°C to +70°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ -10.0-70.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x16 - Temperature Sensor Range 0°C to +80°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 0.0-80.0 °C                                               |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x17 - Temperature Sensor Range +10°C to +90°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 10.0-90.0 °C                                              |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x18 - Temperature Sensor Range +20°C to +100°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 20.0-100.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x19 - Temperature Sensor Range +30°C to +110°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 30.0-110.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x1A - Temperature Sensor Range +40°C to +120°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 40.0-120.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x1B - Temperature Sensor Range +50°C to +130°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 50.0-130.0 °C                                             |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x20 - 10 Bit Temperature Sensor Range -10°C to +41.2°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |1023.0-0.0 ↔ -10.0-41.2 °C                                            |


##### RORG 0xA5 - FUNC 0x02 - TYPE 0x30 - 10 Bit Temperature Sensor Range -40°C to +62.3°C

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |1023.0-0.0 ↔ -40.0-62.3 °C                                            |



##### RORG 0xA5 - FUNC 0x04 - TYPE 0x01 - Range 0°C to +40°C and 0% to 100%

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|HUM     |Rel. Humidity (linear)                            |value   |0.0-250.0 ↔ 0.0-100.0 %                                               |
|TMP     |Temperature (linear)                              |value   |0.0-250.0 ↔ 0.0-40.0 °C                                               |
|TSN     |Availability of the Temperature Sensor            |enum    |0 - not available                                                     |
|        |                                                  |        |1 - available                                                         |


##### RORG 0xA5 - FUNC 0x04 - TYPE 0x02 - Range -20°C to +60°C and 0% to 100%

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|HUM     |Rel. Humidity (linear)                            |value   |0.0-250.0 ↔ 0.0-100.0 %                                               |
|TMP     |Temperature (linear)                              |value   |0.0-255.0 ↔ -20.0-60.0 °C                                             |
|LRNB    |Learn Bit                                         |enum    |0 - Teach-In                                                          |
|        |                                                  |        |1 - Data                                                              |
|TSN     |Availability of the Temperature Sensor            |enum    |0 - not available                                                     |
|        |                                                  |        |1 - available                                                         |


##### RORG 0xA5 - FUNC 0x04 - TYPE 0x03 - Range -20°C to +60°C 10bit-measurement and 0% to 100%

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|HUM     |Rel. Humidity (linear)                            |value   |0.0-255.0 ↔ 0.0-100.0 %                                               |
|TMP     |Temperature (linear)                              |value   |0.0-1023.0 ↔ -20.0-60.0 °C                                            |
|TTP     |Telegram Type                                     |enum    |0 - Heartbeat                                                         |
|        |                                                  |        |1 - Event triggered                                                   |



##### RORG 0xA5 - FUNC 0x06 - TYPE 0x01 - Range 300lx to 60.000lx

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SVC     |Supply voltage (linear)                           |value   |0.0-255.0 ↔ 0.0-5.1 V                                                 |
|ILL2    |Illumination 2 (linear)                           |value   |0.0-255.0 ↔ 300.0-30000.0 lx                                          |
|ILL1    |Illumination 1 (linear)                           |value   |0.0-255.0 ↔ 600.0-60000.0 lx                                          |
|RS      |Range select                                      |enum    |0 - Range acc. to DB_1 (ILL1)                                         |
|        |                                                  |        |1 - Range acc. to DB_2 (ILL2)                                         |


##### RORG 0xA5 - FUNC 0x06 - TYPE 0x02 - Range 0lx to 1.020lx

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SVC     |Supply voltage (linear)                           |value   |0.0-255.0 ↔ 0.0-5.1 V                                                 |
|ILL2    |Illumination 2 (linear)                           |value   |0.0-255.0 ↔ 0.0-510.0 lx                                              |
|ILL1    |Illumination 1 (linear)                           |value   |0.0-255.0 ↔ 0.0-1020.0 lx                                             |
|RS      |Range select                                      |enum    |0 - Range acc. to DB_1 (ILL1)                                         |
|        |                                                  |        |1 - Range acc. to DB_2 (ILL2)                                         |



##### RORG 0xA5 - FUNC 0x07 - TYPE 0x01 - Occupancy with Supply voltage monitor

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SVC     |Supply voltage (OPTIONAL)                         |value   |0.0-250.0 ↔ 0.0-5.0 V                                                 |
|PIR     |PIR Status                                        |enum    |0 - off                                                               |
|        |                                                  |        |1 - on                                                                |



##### RORG 0xA5 - FUNC 0x08 - TYPE 0x01 - Range 0lx to 510lx, 0°C to +51°C and Occupancy Button

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SVC     |Supply voltage (linear)                           |value   |0.0-255.0 ↔ 0.0-5.1 V                                                 |
|ILL     |Illumination (linear)                             |value   |0.0-255.0 ↔ 0.0-510.0 lx                                              |
|TMP     |Temperature (linear)                              |value   |0.0-255.0 ↔ 0.0-51.0 °C                                               |
|PIRS    |PIR Status                                        |enum    |0 - PIR on                                                            |
|        |                                                  |        |1 - PIR off                                                           |
|OCC     |Occupancy Button                                  |enum    |0 - Button pressed                                                    |
|        |                                                  |        |1 - Button released                                                   |



##### RORG 0xA5 - FUNC 0x09 - TYPE 0x0c - VOC sensorNG

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CONC    |VOC                                               |value   |0.0-65535.0 ↔ 0.0-65535.0 ug/m3                                       |
|VOCID   |VOCID                                             |value   |0.0-255.0 ↔ 0.0-255.0 v                                               |
|LRNB    |Learn Bit                                         |enum    |0 - Teach-In                                                          |
|        |                                                  |        |1 - Data                                                              |
|Unit    |Unit                                              |enum    |0 - ppb                                                               |
|        |                                                  |        |1 - ug/m3                                                             |
|SCM     |Scale Multiplier                                  |enum    |0 - 0.01                                                              |
|        |                                                  |        |1 - 0.1                                                               |
|        |                                                  |        |2 - 1                                                                 |
|        |                                                  |        |3 - 10                                                                |


##### RORG 0xA5 - FUNC 0x09 - TYPE 0x04 - CO2 Sensor

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|HUM     |Rel. Humidity (linear)                            |value   |0.0-200.0 ↔ 0.0-100.0 %                                               |
|Conc    |Concentration (linear)                            |value   |0.0-255.0 ↔ 0.0-2550.0 ppm                                            |
|TMP     |Temperature (linear)                              |value   |0.0-255.0 ↔ 0.0-51.0 °C                                               |


##### RORG 0xA5 - FUNC 0x09 - TYPE 0x05 - VOC Sensor

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|Conc    |VOC Concentration                                 |value   |0.0-65535.0 ↔ 0.0-65535.0 ppb                                         |
|VOC_ID  |VOC Identification                                |enum    |0 - VOCT (total)                                                      |
|        |                                                  |        |1 - Formaldehyde                                                      |
|        |                                                  |        |2 - Benzene                                                           |
|        |                                                  |        |3 - Styrene                                                           |
|        |                                                  |        |4 - Toluene                                                           |
|        |                                                  |        |5 - Tetrachloroethylene                                               |
|        |                                                  |        |6 - Xylene                                                            |
|        |                                                  |        |7 - n-Hexane                                                          |
|        |                                                  |        |8 - n-Octane                                                          |
|        |                                                  |        |9 - Cyclopentane                                                      |
|        |                                                  |        |10 - Methanol                                                         |
|        |                                                  |        |11 - Ethanol                                                          |
|        |                                                  |        |12 - 1-Pentanol                                                       |
|        |                                                  |        |13 - Acetone                                                          |
|        |                                                  |        |14 - ethylene Oxide                                                   |
|        |                                                  |        |15 - Acetaldehyde ue                                                  |
|        |                                                  |        |16 - Acetic Acid                                                      |
|        |                                                  |        |17 - Propionice Acid                                                  |
|        |                                                  |        |18 - ValericAcid                                                      |
|        |                                                  |        |19 - ButyricAcid                                                      |
|        |                                                  |        |20 - Ammoniac                                                         |
|        |                                                  |        |22 - Hydrogen Sulfide                                                 |
|        |                                                  |        |23 - Dimethylsulfide                                                  |
|        |                                                  |        |24 - 2-Butanol (butyl Alcohol)                                        |
|        |                                                  |        |25 - 2-Methylpropanol                                                 |
|        |                                                  |        |26 - Diethyl ether                                                    |
|        |                                                  |        |255 - ozone                                                           |


##### RORG 0xA5 - FUNC 0x09 - TYPE 0x06 - Radon

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|ACT     |Radon                                             |value   |0.0-1023.0 ↔ 0.0-1023.0 bq/m3                                         |
|LRNB    |Learn Bit                                         |enum    |0 - Teach-In                                                          |
|        |                                                  |        |1 - Data                                                              |


##### RORG 0xA5 - FUNC 0x09 - TYPE 0x07 - Particles

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|PM10    |Particles_10                                      |value   |0.0-511.0 ↔ 0.0-511.0 ug/m3                                           |
|PM2.5   |Particles_2.5                                     |value   |0.0-511.0 ↔ 0.0-511.0 ug/m3                                           |
|PM1     |Particles_1                                       |value   |0.0-511.0 ↔ 0.0-511.0 ug/m3                                           |
|LRNB    |Learn Bit                                         |enum    |0 - Teach-In                                                          |
|        |                                                  |        |1 - Data                                                              |
|PM10a   |PM10 Active                                       |enum    |0 - PM10 not active                                                   |
|        |                                                  |        |1 - PM10 active                                                       |
|PM2.5a  |PM2.5 Active                                      |enum    |0 - PM2.5 not active                                                  |
|        |                                                  |        |1 - PM2.5 active                                                      |
|PM1a    |PM1 Active                                        |enum    |0 - PM1 not active                                                    |
|        |                                                  |        |1 - PM1 active                                                        |



##### RORG 0xA5 - FUNC 0x10 - TYPE 0x03 - Temperature Sensor and Set Point

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SP      |Set Point (linear)                                |value   |0.0-255.0 ↔ 0.0-255.0 %                                               |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 0.0-40.0 °C                                               |


##### RORG 0xA5 - FUNC 0x10 - TYPE 0x05 - Temperature Sensor, Set Point and Occupancy Control

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SP      |Set Point (linear)                                |value   |0.0-255.0 ↔ 0.0-255.0 %                                               |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 0.0-40.0 °C                                               |
|OCC     |Occupancy Button                                  |enum    |0 - Button pressed                                                    |
|        |                                                  |        |1 - Button released                                                   |


##### RORG 0xA5 - FUNC 0x10 - TYPE 0x06 - Temperature Sensor, Set Point and Day/Night Control

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SP      |Set Point (linear)                                |value   |0.0-255.0 ↔ 0.0-255.0 %                                               |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 0.0-40.0 °C                                               |
|SLSW    |Slide switch                                      |enum    |0 - Position I / Night / Off                                          |
|        |                                                  |        |1 - Position O / Day / On                                             |


##### RORG 0xA5 - FUNC 0x10 - TYPE 0x10 - Temperature and Humidity Sensor, Set Point and Occupancy Control

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SP      |Set Point (linear)                                |value   |0.0-255.0 ↔ 0.0-255.0                                                 |
|HUM     |Rel. Humidity (linear)                            |value   |0.0-250.0 ↔ 0.0-100.0 %                                               |
|TMP     |Temperature (linear)                              |value   |0.0-250.0 ↔ 0.0-40.0 °C                                               |
|OCC     |Occupancy Button                                  |enum    |0 - Button pressed                                                    |
|        |                                                  |        |1 - Button released                                                   |


##### RORG 0xA5 - FUNC 0x10 - TYPE 0x12 - Temperature and Humidity Sensor and Set Point

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SP      |Set Point (linear)                                |value   |0.0-255.0 ↔ 0.0-255.0                                                 |
|HUM     |Rel. Humidity (linear)                            |value   |0.0-250.0 ↔ 0.0-100.0 %                                               |
|TMP     |Temperature (linear)                              |value   |0.0-250.0 ↔ 0.0-40.0 °C                                               |



##### RORG 0xA5 - FUNC 0x11 - TYPE 0x02 - Temperature Controller Output

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CVAR    |Actual value of controller                        |value   |0.0-255.0 ↔ 0.0-100.0 %                                               |
|FAN     |Actual value of fan                               |enum    |0 - State 0 Manual                                                    |
|        |                                                  |        |1 - State 1 Manual                                                    |
|        |                                                  |        |2 - State 2 Manual                                                    |
|        |                                                  |        |3 - State 3 Manual                                                    |
|        |                                                  |        |16 - State 0 Automatic                                                |
|        |                                                  |        |17 - State 1 Automatic                                                |
|        |                                                  |        |18 - State 2 Automatic                                                |
|        |                                                  |        |19 - State 3 Automatic                                                |
|        |                                                  |        |255 - Not Available                                                   |
|ASP     |Actual Setpoint                                   |value   |0.0-255.0 ↔ 0.0-51.2 C                                                |
|ALR     |Alarm                                             |enum    |0 - No alarm                                                          |
|        |                                                  |        |1 - Alarm                                                             |
|CTM     |Controller mode                                   |enum    |1 - Heating                                                           |
|        |                                                  |        |2 - Cooling                                                           |
|        |                                                  |        |3 - Off                                                               |
|CTS     |Controller state                                  |enum    |0 - Automatic                                                         |
|        |                                                  |        |1 - Override                                                          |
|ERH     |Energy hold-off                                   |enum    |0 - Normal                                                            |
|        |                                                  |        |1 - Energy hold-off / Dew point                                       |
|RO      |Room occupancy                                    |enum    |0 - Occupied                                                          |
|        |                                                  |        |1 - Unoccupied                                                        |
|        |                                                  |        |2 - StandBy                                                           |
|        |                                                  |        |3 - Frost                                                             |


##### RORG 0xA5 - FUNC 0x11 - TYPE 0x03 - Blind Status

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|BSP     |Blind/shutter position                            |value   |0.0-100.0 ↔ 0.0-100.0 %                                               |
|AS      |Angle sign                                        |enum    |0 - Positive sign                                                     |
|        |                                                  |        |1 - Negative sign                                                     |
|AN      |Angle in 2 degrees steps                          |value   |0.0-90.0 ↔ 0.0-180.0 degrees                                          |
|PVF     |Position value flag                               |enum    |0 - No position value available                                       |
|        |                                                  |        |1 - Position value available                                          |
|AVF     |Angle value flag                                  |enum    |0 - No Angle value available                                          |
|        |                                                  |        |1 - Angle value available                                             |
|ES      |Error state                                       |enum    |0 - No error present                                                  |
|        |                                                  |        |1 - End-positions are not configured                                  |
|        |                                                  |        |2 - Internal failure                                                  |
|        |                                                  |        |3 - Not used                                                          |
|EP      |End position                                      |enum    |0 - No End-position available                                         |
|        |                                                  |        |1 - No End-position reached                                           |
|        |                                                  |        |2 - Blind fully open                                                  |
|        |                                                  |        |3 - Blind fully closed                                                |
|ST      |Status                                            |enum    |0 - No status available                                               |
|        |                                                  |        |1 - Blind is stopped                                                  |
|        |                                                  |        |2 - Blind opens                                                       |
|        |                                                  |        |3 - Blind closes                                                      |
|SM      |Service mode                                      |enum    |0 - Normal mode                                                       |
|        |                                                  |        |1 - Service mode activated                                            |
|MOTP    |Mode of the position                              |enum    |0 - Normal mode                                                       |
|        |                                                  |        |1 - Inverse ode                                                       |



##### RORG 0xA5 - FUNC 0x13 - TYPE 0x01 - Weather Station

###### command: 1
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|DWS     |Dawn sensor                                       |value   |0.0-255.0 ↔ 0.0-999.0 lx                                              |
|TMP     |Outdoor Temp                                      |value   |0.0-255.0 ↔ -40.0-80.0 °C                                             |
|WND     |Wind speed                                        |value   |0.0-255.0 ↔ 0.0-70.0 m/s                                              |
|D/N     |Day / Night                                       |enum    |0 - day                                                               |
|        |                                                  |        |1 - night                                                             |
|RAN     |Rain Indication                                   |enum    |0 - no rain                                                           |
|        |                                                  |        |1 - rain                                                              |

###### command: 2
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SNW     |Sun - West                                        |value   |0.0-255.0 ↔ 0.0-150.0 klx                                             |
|SNS     |Sun - South                                       |value   |0.0-255.0 ↔ 0.0-150.0 klx                                             |
|SNE     |Sun - East                                        |value   |0.0-255.0 ↔ 0.0-150.0 klx                                             |
|HEM     |Hemisphere                                        |enum    |0 - North                                                             |
|        |                                                  |        |1 - South                                                             |

###### command: 3
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|DY      |Day                                               |value   |1.0-31.0 ↔ 1.0-31.0                                                   |
|MTH     |Month                                             |value   |1.0-12.0 ↔ 1.0-12.0                                                   |
|YR      |Year                                              |value   |0.0-99.0 ↔ 2000.0-2099.0                                              |
|SRC     |Source                                            |enum    |0 - Real Time Clock                                                   |
|        |                                                  |        |1 - GPS or equivalent                                                 |

###### command: 4
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|WDY     |Weekday                                           |enum    |1 - Monday                                                            |
|        |                                                  |        |2 - Tuesday                                                           |
|        |                                                  |        |3 - Wednesday                                                         |
|        |                                                  |        |4 - Thursday                                                          |
|        |                                                  |        |5 - Friday                                                            |
|        |                                                  |        |6 - Saturday                                                          |
|        |                                                  |        |7 - Sunday                                                            |
|HR      |Hour                                              |value   |0.0-23.0 ↔ 0.0-23.0                                                   |
|MIN     |Minute                                            |value   |0.0-59.0 ↔ 0.0-59.0                                                   |
|SEC     |Second                                            |value   |0.0-59.0 ↔ 0.0-59.0                                                   |
|TMF     |Time Format                                       |enum    |0 - 24 Hours                                                          |
|        |                                                  |        |1 - 12 Hours                                                          |
|A/PM    |AM/PM                                             |enum    |0 - AM                                                                |
|        |                                                  |        |1 - PM                                                                |
|SRC     |Source                                            |enum    |0 - Real Time Clock                                                   |
|        |                                                  |        |1 - GPS or equivalent                                                 |

###### command: 5
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|ELV     |Elevation                                         |value   |0.0-180.0 ↔ -90.0-90.0 °                                              |
|AZM     |Azimut                                            |value   |0.0-359.0 ↔ 0.0-359.0 °                                               |

###### command: 6
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|LAT(MSB)|Latitude(MSB)                                     |value   |0.0-15.0 ↔ 0.0-15.0                                                   |
|LOT(MSB)|Longitude(MSB)                                    |value   |0.0-15.0 ↔ 0.0-15.0                                                   |
|LAT(LSB)|Latitude(LSB)                                     |value   |0.0-255.0 ↔ 0.0-255.0                                                 |
|LOT(LSB)|Longitude(LSB)                                    |value   |0.0-255.0 ↔ 0.0-255.0                                                 |



##### RORG 0xA5 - FUNC 0x14 - TYPE 0x01 - Single Input Contact (Window/Door), Supply voltage monitor

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SVC     |Supply voltage / super cap. (linear); 251 - 255 reserved for error code|value   |0.0-250.0 ↔ 0.0-5.0 V                                                 |
|CT      |Contact                                           |enum    |1 - open                                                              |
|        |                                                  |        |0 - closed                                                            |



##### RORG 0xA5 - FUNC 0x20 - TYPE 0x01 - Battery Powered Actuator (BI-DIR)

###### direction: 1
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CV      |Current Value                                     |value   |0.0-100.0 ↔ 0.0-100.0 %                                               |
|SO      |Service On                                        |enum    |0 - off                                                               |
|        |                                                  |        |1 - on                                                                |
|ENIE    |Energy input enabled                              |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|ES      |Energy storage sufficiently charged               |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|BCAP    |Battery capacity; change battery next days        |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|CCO     |Contact, cover open                               |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|FTS     |Failure Temperature sensor, out of range          |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|DWO     |Detection, window open                            |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|ACO     |Actuator obstructed                               |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|TMP     |Temperature (linear)                              |value   |0.0-255.0 ↔ 0.0-40.0 °C                                               |

###### direction: 2
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SP      |Valve Position or Temperature Setpoint            |value   |0.0-100.0 ↔ 0.0-100.0 %                                               |
|TMP     |Temperature from RCU                              |value   |0.0-255.0 ↔ 0.0-40.0 °C                                               |
|RIN     |Run init sequence                                 |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|LFS     |Lift set                                          |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|VO      |Valve open / maintenance                          |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|VC      |Valve closed                                      |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|SB      |Summer bit, Reduction of energy consumption       |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|SPS     |Set point selection                               |enum    |0 - Valve position                                                    |
|        |                                                  |        |1 - Temperature set point                                             |
|SPN     |Set point inverse                                 |enum    |0 - false                                                             |
|        |                                                  |        |1 - true                                                              |
|RCU     |Select function                                   |enum    |0 - RCU                                                               |
|        |                                                  |        |1 - service on                                                        |



##### RORG 0xA5 - FUNC 0x12 - TYPE 0x00 - Counter

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|MR      |current value in W or cumulative value in kWh     |value   |0.0-16777215.0 ↔ 0.0-16777215.0                                       |
|CH      |Channel                                           |value   |0.0-15.0 ↔ 0.0-15.0 1                                                 |
|LRNB    |Learn Bit                                         |enum    |0 - Teach-In                                                          |
|        |                                                  |        |1 - Data                                                              |
|DT      |Current value or cumulative value                 |enum    |0 - kWh                                                               |
|        |                                                  |        |1 - W                                                                 |
|DIV     |Divisor for value                                 |enum    |0 - x/1                                                               |
|        |                                                  |        |1 - x/10                                                              |
|        |                                                  |        |2 - x/100                                                             |
|        |                                                  |        |3 - x/1000                                                            |


##### RORG 0xA5 - FUNC 0x12 - TYPE 0x01 - Electricity

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|MR      |current value in W or cumulative value in kWh     |value   |0.0-16777215.0 ↔ 0.0-16777215.0                                       |
|TI      |Tariff info                                       |value   |0.0-15.0 ↔ 0.0-15.0                                                   |
|DT      |Current value or cumulative value                 |enum    |0 - kWh                                                               |
|        |                                                  |        |1 - W                                                                 |
|DIV     |Divisor for value                                 |enum    |0 - x/1                                                               |
|        |                                                  |        |1 - x/10                                                              |
|        |                                                  |        |2 - x/100                                                             |
|        |                                                  |        |3 - x/1000                                                            |



##### RORG 0xA5 - FUNC 0x30 - TYPE 0x03 - Digital Inputs, Wake and Temperature

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature (linear)                              |value   |255.0-0.0 ↔ 0.0-40.0 °C                                               |
|WA0     |Value of wake signal                              |enum    |0 - Low                                                               |
|        |                                                  |        |1 - High                                                              |
|DI3     |Digital Input 3                                   |enum    |0 - Low                                                               |
|        |                                                  |        |1 - High                                                              |
|DI2     |Digital Input 2                                   |enum    |0 - Low                                                               |
|        |                                                  |        |1 - High                                                              |
|DI1     |Digital Input 1                                   |enum    |0 - Low                                                               |
|        |                                                  |        |1 - High                                                              |
|DI0     |Digital Input 0                                   |enum    |0 - Low                                                               |
|        |                                                  |        |1 - High                                                              |



##### RORG 0xA5 - FUNC 0x38 - TYPE 0x08 - Gateway

###### command: 1
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|COM     |Command ID                                        |enum    |0-13 - Command ID {value}                                             |
|TIM     |Time in 1/10 seconds. 0 = no time specifed        |value   |1.0-65535.0 ↔ 0.1-6553.5 s                                            |
|LCK     |Lock for duration time if time >0, unlimited time of no time specified. Locking may be cleared with "unlock". During lock phase no other commands will be accepted or executed|enum    |0 - Unlock                                                            |
|        |                                                  |        |1 - Lock                                                              |
|DEL     |Delay or duration (if Time > 0); 0 = Duration (Execute switching command immediately and switch back after duration) 1 = Delay (Execute switching command after delay)|enum    |0 - Duration                                                          |
|        |                                                  |        |1 - Delay                                                             |
|SW      |Switching command ON/OFF                          |enum    |0 - Off                                                               |
|        |                                                  |        |1 - On                                                                |

###### command: 2
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|COM     |Command ID                                        |enum    |0-13 - Command ID {value}                                             |
|EDIM    |Dimming value (absolute [0...255] or relative [0...100])|value   |0.0-255.0 ↔ 0.0-255.0 %                                               |
|RMP     |Ramping time in seconds, 0 = no ramping, 1...255 = seconds to 100%|value   |0.0-255.0 ↔ 0.0-255.0 s                                               |
|EDIMR   |Dimming Range                                     |enum    |0 - Absolute value                                                    |
|        |                                                  |        |1 - Relative value                                                    |
|STR     |Store final value                                 |enum    |0 - No                                                                |
|        |                                                  |        |1 - Yes                                                               |
|SW      |Switching command                                 |enum    |0 - Off                                                               |
|        |                                                  |        |1 - On                                                                |



### VLD Telegram (0xD2)
##### RORG 0xD2 - FUNC 0x01 - TYPE 0x01 - Electronic switch with Local Control

###### command: 4
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|PF      |Power Failure                                     |enum    |0 - Power Failure Detection disabled/not supported                    |
|        |                                                  |        |1 - Power Failure Detection enabled                                   |
|PFD     |Power Failure Detection                           |enum    |0 - Power Failure Detection not detected/not supported/disabled       |
|        |                                                  |        |1 - Power Failure Detection Detected                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|OC      |Over current switch off                           |enum    |0 - Over current switch off: ready / not supported                    |
|        |                                                  |        |1 - Over current switch off: executed                                 |
|EL      |Error level                                       |enum    |0 - Error level 0: hardware OK                                        |
|        |                                                  |        |1 - Error level 1: hardware warning                                   |
|        |                                                  |        |2 - Error level 2: hardware failure                                   |
|        |                                                  |        |3 - Error level not supported                                         |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|LC      |Local control                                     |enum    |0 - Local control disabled / not supported                            |
|        |                                                  |        |1 - Local control enabled                                             |
|OV      |Output value                                      |enum    |0 - Output value 0% or OFF                                            |
|        |                                                  |        |1-100 - Output value {value}% or ON                                   |
|        |                                                  |        |101-126 - Not used                                                    |
|        |                                                  |        |127 - output value not valid / not set                                |

###### command: 1
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|DV      |Dim value                                         |enum    |0 - Switch to new output value                                        |
|        |                                                  |        |1 - Dim to new output level - dim timer 1                             |
|        |                                                  |        |2 - Dim to new output level - dim timer 2                             |
|        |                                                  |        |3 - Dim to new output level - dim timer 3                             |
|        |                                                  |        |4 - Stop dimming                                                      |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - All output channels supported by the device                      |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|OV      |Output value                                      |enum    |0 - Output value 0% or OFF                                            |
|        |                                                  |        |1-100 - Output value {value}% or ON                                   |
|        |                                                  |        |101-126 - Not used                                                    |
|        |                                                  |        |127 - output value not valid / not set                                |


##### RORG 0xD2 - FUNC 0x01 - TYPE 0x12 - Electronic switch with Local Control

###### command: 4
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|PF      |Power Failure                                     |enum    |0 - Power Failure Detection disabled/not supported                    |
|        |                                                  |        |1 - Power Failure Detection enabled                                   |
|PFD     |Power Failure Detection                           |enum    |0 - Power Failure Detection not detected/not supported/disabled       |
|        |                                                  |        |1 - Power Failure Detection Detected                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|OC      |Over current switch off                           |enum    |0 - Over current switch off: ready / not supported                    |
|        |                                                  |        |1 - Over current switch off: executed                                 |
|EL      |Error level                                       |enum    |0 - Error level 0: hardware OK                                        |
|        |                                                  |        |1 - Error level 1: hardware warning                                   |
|        |                                                  |        |2 - Error level 2: hardware failure                                   |
|        |                                                  |        |3 - Error level not supported                                         |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|LC      |Local control                                     |enum    |0 - Local control disabled / not supported                            |
|        |                                                  |        |1 - Local control enabled                                             |
|OV      |Output value                                      |enum    |0 - Output value 0% or OFF                                            |
|        |                                                  |        |1-100 - Output value {value}% or ON                                   |
|        |                                                  |        |101-126 - Not used                                                    |
|        |                                                  |        |127 - output value not valid / not set                                |

###### command: 1
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|DV      |Dim value                                         |enum    |0 - Switch to new output value                                        |
|        |                                                  |        |1 - Dim to new output level - dim timer 1                             |
|        |                                                  |        |2 - Dim to new output level - dim timer 2                             |
|        |                                                  |        |3 - Dim to new output level - dim timer 3                             |
|        |                                                  |        |4 - Stop dimming                                                      |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - All output channels supported by the device                      |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|OV      |Output value                                      |enum    |0 - Output value 0% or OFF                                            |
|        |                                                  |        |1-100 - Output value {value}% or ON                                   |
|        |                                                  |        |101-126 - Not used                                                    |
|        |                                                  |        |127 - output value not valid / not set                                |

###### command: 2
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|DE      |Taught-in devices                                 |enum    |0 - Disable taught-in devices (with different EEP)                    |
|        |                                                  |        |1 - Enable taught-in devices (with different EEP)                     |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|OC      |Over shut down                                    |enum    |0 - Over current shut down: static off                                |
|        |                                                  |        |1 - Over current shut down: automatic restart                         |
|RO      |Reset over current shut down                      |enum    |0 - Reset over current shut down: not active                          |
|        |                                                  |        |1 - Reset over current shut down: trigger signal                      |
|LC      |Local Control                                     |enum    |0 - Disable local control                                             |
|        |                                                  |        |1 - Enable local control                                              |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|DT2     |Dim timer 2                                       |enum    |0 - Not used                                                          |
|        |                                                  |        |1-15 - Dim time {value} x 0.5s                                        |
|DT3     |Dim timer 3                                       |enum    |0 - Not used                                                          |
|        |                                                  |        |1-15 - Dim time {value} x 0.5s                                        |
|DN      |User interface indication                         |enum    |0 - Day Operation                                                     |
|        |                                                  |        |1 - Night Operation                                                   |
|PF      |Power Failure                                     |enum    |0 - Disable Power Failure Detection                                   |
|        |                                                  |        |1 - Enable Power Failure Detection                                    |
|DS      |Default State                                     |enum    |0 - Default state: 0% or OFF                                          |
|        |                                                  |        |1 - Default state: 100% or ON                                         |
|        |                                                  |        |2 - Remember Last State                                               |
|        |                                                  |        |3 - Not used                                                          |
|DT1     |Dim timer 1                                       |enum    |0 - Not used                                                          |
|        |                                                  |        |1-15 - Dim time {value} x 0.5s                                        |

###### command: 3
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - All output channels supported by the device                      |
|        |                                                  |        |31 - Input channel (from mains supply)                                |

###### command: 5
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|RM      |Report measurement                                |enum    |0 - Report measurement: query only                                    |
|        |                                                  |        |1 - Report measurement: query / auto reporting                        |
|RE      |Reset measurement                                 |enum    |0 - Reset measurement: not active                                     |
|        |                                                  |        |1 - Reset measurement: trigger signal                                 |
|EP      |Measurement mode                                  |enum    |0 - Energy measurement                                                |
|        |                                                  |        |1 - Power measurement                                                 |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|MDLSB   |Measurement delta to be reported (LSB)            |value   |0.0-15.0 ↔ 0.0-15.0                                                   |
|UN      |Unit                                              |enum    |0 - Energy [Ws]                                                       |
|        |                                                  |        |1 - Energy [Wh]                                                       |
|        |                                                  |        |2 - Energy [KWh]                                                      |
|        |                                                  |        |3 - Power [W]                                                         |
|        |                                                  |        |4 - Power [KW]                                                        |
|MDMSB   |Measurement delta to be reported (MSB)            |value   |0.0-255.0 ↔ 0.0-255.0                                                 |
|MAT     |Maximum time between two subsequent actuator messages|value   |1.0-255.0 ↔ 10.0-2550.0 s                                             |
|MIT     |Minimum time between two subsequent actuator messages|value   |1.0-255.0 ↔ 1.0-255.0 s                                               |

###### command: 6
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|QU      |Query                                             |enum    |0 - Query energy                                                      |
|        |                                                  |        |1 - Query power                                                       |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |

###### command: 7
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|UN      |Unit                                              |enum    |0 - Energy [Ws]                                                       |
|        |                                                  |        |1 - Energy [Wh]                                                       |
|        |                                                  |        |2 - Energy [KWh]                                                      |
|        |                                                  |        |3 - Power [W]                                                         |
|        |                                                  |        |4 - Power [KW]                                                        |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|MV      |Measurement value                                 |value   |0.0-4294967295.0 ↔ 0.0-4294967295.0                                   |

###### command: 8
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|PM      |PilotWireMode                                     |enum    |0 - Off                                                               |
|        |                                                  |        |1 - Comfort                                                           |
|        |                                                  |        |2 - Eco                                                               |
|        |                                                  |        |3 - Anti-freeze                                                       |
|        |                                                  |        |4 - Comfort-1                                                         |
|        |                                                  |        |5 - Comfort-2                                                         |

###### command: 9
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |

###### command: 10
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|PM      |PilotWireMode                                     |enum    |0 - Off                                                               |
|        |                                                  |        |1 - Comfort                                                           |
|        |                                                  |        |2 - Eco                                                               |
|        |                                                  |        |3 - Anti-freeze                                                       |
|        |                                                  |        |4 - Comfort-1                                                         |
|        |                                                  |        |5 - Comfort-2                                                         |

###### command: 11
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|AOT     |Auto Off Timer                                    |enum    |0 - Timer deactivated                                                 |
|        |                                                  |        |1-65534 - Timer to automatically set OFF output channel when it is set ON|
|        |                                                  |        |65535 - Does not modify saved value                                   |
|DOT     |Delay OFF Timer                                   |enum    |0 - Timer deactivated                                                 |
|        |                                                  |        |1-65534 - Timer to automatically set OFF output channel when it is set ON|
|        |                                                  |        |65535 - Does not modify saved value                                   |
|EBM     |External Switch/Push Button                       |enum    |0 - Not applicable                                                    |
|        |                                                  |        |1 - External Switch                                                   |
|        |                                                  |        |2 - External Push Button                                              |
|        |                                                  |        |3 - Auto detect                                                       |
|SWT     |2-state switch                                    |enum    |0 - Change of key state sets ON or OFF                                |
|        |                                                  |        |1 - Specific ON/OFF positions. ON when contacts are closed. OFF when contacts are open.|

###### command: 12
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |

###### command: 13
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CMD     |Command indentifier                               |enum    |0-13 - Command ID {value}                                             |
|IO      |I/O channel                                       |enum    |0-29 - Output channel {value} (to load)                               |
|        |                                                  |        |30 - Not applicable, do not use                                       |
|        |                                                  |        |31 - Input channel (from mains supply)                                |
|AOT     |Auto Off Timer                                    |enum    |0 - Timer deactivated                                                 |
|        |                                                  |        |1-65534 - Timer to automatically set OFF output channel when it is set ON|
|        |                                                  |        |65535 - Does not modify saved value                                   |
|DOT     |Delay OFF Timer                                   |enum    |0 - Timer deactivated                                                 |
|        |                                                  |        |1-65534 - Timer to automatically set OFF output channel when it is set ON|
|        |                                                  |        |65535 - Does not modify saved value                                   |
|EBM     |External Switch/Push Button                       |enum    |0 - Not applicable                                                    |
|        |                                                  |        |1 - External Switch                                                   |
|        |                                                  |        |2 - External Push Button                                              |
|        |                                                  |        |3 - Auto detect                                                       |
|SWT     |2-state switch                                    |enum    |0 - Change of key state sets ON or OFF                                |
|        |                                                  |        |1 - Specific ON/OFF positions. ON when contacts are closed. OFF when contacts are open.|



##### RORG 0xD2 - FUNC 0x05 - TYPE 0x00 - Type 0x00

###### command: 1
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|POS     |Vertical position                                 |enum    |0-100 - Output position {value}%                                      |
|        |                                                  |        |127 - Do not change                                                   |
|ANG     |Rotation angle                                    |enum    |0-100 - Output angle {value}%                                         |
|        |                                                  |        |127 - Do not change                                                   |
|REPO    |Repositioning                                     |enum    |0 - Go directly to POS/ANG                                            |
|        |                                                  |        |1 - Go up (0%), then to POS/ANG                                       |
|        |                                                  |        |2 - Go down (100%), then to POS/ANG                                   |
|        |                                                  |        |3 - Reserved                                                          |
|LOCK    |Locking modes                                     |enum    |0 - Do not change                                                     |
|        |                                                  |        |1 - Set blockage mode                                                 |
|        |                                                  |        |2 - Set alarm mode                                                    |
|        |                                                  |        |3 - Reserved                                                          |
|        |                                                  |        |4 - Reserved                                                          |
|        |                                                  |        |5 - Reserved                                                          |
|        |                                                  |        |6 - Reserved                                                          |
|        |                                                  |        |7 - Deblockage                                                        |
|CHN     |Channel                                           |enum    |0 - Channel 1                                                         |
|CMD     |Command Id                                        |enum    |0-5 - Command ID {value}                                              |

###### command: 2
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CHN     |Channel                                           |enum    |0 - Channel 1                                                         |
|CMD     |Command Id                                        |enum    |0-5 - Command ID {value}                                              |

###### command: 3
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|CHN     |Channel                                           |enum    |0 - Channel 1                                                         |
|CMD     |Command Id                                        |enum    |0-5 - Command ID {value}                                              |

###### command: 4
|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|POS     |Vertical position                                 |enum    |0-100 - Output position {value}%                                      |
|        |                                                  |        |127 - Do not change                                                   |
|ANG     |Rotation angle                                    |enum    |0-100 - Output angle {value}%                                         |
|        |                                                  |        |127 - Do not change                                                   |
|REPO    |Repositioning                                     |enum    |0 - Go directly to POS/ANG                                            |
|        |                                                  |        |1 - Go up (0%), then to POS/ANG                                       |
|        |                                                  |        |2 - Go down (100%), then to POS/ANG                                   |
|        |                                                  |        |3 - Reserved                                                          |
|LOCK    |Locking modes                                     |enum    |0 - Do not change                                                     |
|        |                                                  |        |1 - Set blockage mode                                                 |
|        |                                                  |        |2 - Set alarm mode                                                    |
|        |                                                  |        |3 - Reserved                                                          |
|        |                                                  |        |4 - Reserved                                                          |
|        |                                                  |        |5 - Reserved                                                          |
|        |                                                  |        |6 - Reserved                                                          |
|        |                                                  |        |7 - Deblockage                                                        |
|CHN     |Channel                                           |enum    |0 - Channel 1                                                         |
|CMD     |Command Id                                        |enum    |0-5 - Command ID {value}                                              |



##### RORG 0xD2 - FUNC 0x14 - TYPE 0x41 - Indoor -Temperature, Humidity XYZ Acceleration, Illumination Sensor

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|TMP     |Temperature 10                                    |value   |0.0-1000.0 ↔ -40.0-60.0 °C                                            |
|HUM     |Rel. Humidity linear)                             |value   |0.0-200.0 ↔ 0.0-100.0 %                                               |
|ILL     |Illumination linear)                              |value   |0.0-100000.0 ↔ 0.0-100000.0 lx                                        |
|ACC     |Acceleration Status                               |enum    |0 - Periodic Update                                                   |
|        |                                                  |        |1 - Threshold 1 exceeded                                              |
|        |                                                  |        |2 - Threshold 2 exceeded                                              |
|ACX     |Absolute Acceleration on X axis                   |value   |0.0-1000.0 ↔ -2.5-2.5 g                                               |
|ACY     |Absolute Acceleration on Y axis                   |value   |0.0-1000.0 ↔ -2.5-2.5 g                                               |
|ACZ     |Absolute Acceleration on Z axis                   |value   |0.0-1000.0 ↔ -2.5-2.5 g                                               |
|CO      |Contact                                           |enum    |0 - Open                                                              |
|        |                                                  |        |1 - Closed                                                            |


##### RORG 0xD2 - FUNC 0x14 - TYPE 0x30 - Smoke Alarm Humidity Temperature Confort Air

|shortcut|description                                       |type    |values                                                                |
|--------|--------------------------------------------------|--------|----                                                                  |
|SMAS    |Smoke Alarm status                                |enum    |0 - Smoke Alarm non-activated                                         |
|        |                                                  |        |1 - Smoke Alarm activated                                             |
|SFMD    |Sensor fault mode status                          |enum    |0 - Sensor Fault mode non-activated                                   |
|        |                                                  |        |1 - Sensor Fault mode activated                                       |
|SMACAM  |Smoke Alarm Condition analysis: Maintenance       |enum    |0 - Maintenance OK                                                    |
|        |                                                  |        |1 - Maintenance not done                                              |
|SMACAH  |Smoke Alarm Condition analysis: Humidity          |enum    |0 - Humidity range OK                                                 |
|        |                                                  |        |1 - Humidity range NOK                                                |
|SMACAT  |Smoke Alarm Condition analysis: Temperature       |enum    |0 - Temperature range OK                                              |
|        |                                                  |        |1 - Temperature range NOK                                             |
|TSLM    |Time since last maintenance                       |value   |0.0-250.0 ↔ 0.0-250.0 week                                            |
|        |                                                  |        |255 - Error                                                           |
|ES      |Energy Storage                                    |enum    |0 - High                                                              |
|        |                                                  |        |1 - Medium                                                            |
|        |                                                  |        |2 - Low                                                               |
|        |                                                  |        |3 - Critical                                                          |
|RPLT    |Remaining product life time                       |value   |0.0-120.0 ↔ 0.0-120.0 month                                           |
|        |                                                  |        |255 - Error                                                           |
|TMP8    |Temperature (linear)                              |value   |0.0-250.0 ↔ 0.0-50.0 °C                                               |
|        |                                                  |        |255 - Error                                                           |
|HUM     |Humidity (linear)                                 |value   |0.0-200.0 ↔ 0.0-100.0 %                                               |
|        |                                                  |        |255 - Error                                                           |
|HCI     |Hygrothermal Confort                              |enum    |0 - Good                                                              |
|        |                                                  |        |1 - Medium                                                            |
|        |                                                  |        |2 - Bad                                                               |
|        |                                                  |        |3 - Error                                                             |
|IAQTH   |T/Hum. Indoor Air Analysis                        |enum    |0 - Optimal air range                                                 |
|        |                                                  |        |1 - Dry Air range                                                     |
|        |                                                  |        |2 - High humidity range                                               |
|        |                                                  |        |3 - High temperature and humidity range                               |
|        |                                                  |        |4 - Temperature or Humidity out of analysis range                     |
|        |                                                  |        |5 - Reserved                                                          |
|        |                                                  |        |6 - Reserved                                                          |
|        |                                                  |        |7 - Error                                                             |



