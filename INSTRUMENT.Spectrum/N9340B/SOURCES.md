# Sources — N9340B.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## Keysight N9340B Handheld Spectrum Analyzer Programmer's Guide (N9340-90010)

Edition 2, July 2014 — Command Reference — <https://propribory.ru/data/upload/static/files/N9340-90010progr.pdf>

| Command | Change | Manual |
|---|---|---|
| `set/Set_Measure_Semask_Offset_List_Sweep` | arg = `{"kind": "numeric", "unit": "s", "min": 0.005, "max": 4000}` | :MEASure:SEMask:OFFSet:LIST:SWEeptime, p. 71 — <time> (up to five values), Range 5 ms to 4 ks — a time, not an enum |
| `set/Set_Measure_Semask_Sweep` | arg = `{"kind": "numeric", "unit": "s", "min": 0.00837, "max": 4000}` | :MEASure:SEMask:SWEeptime, p. 74 — <number>, Range 8.37 ms through 4 ks, *RST Auto |
| `set/Set_System_Channel` | arg = `{"kind": "bool", "values": ["OFF", "ON"]}` | :SYSTem:CHANnel, p. 87 — OFF|ON|0|1 — switches to the low-frequency channel |
| `set/Set_Trace_Mode` | arg = `{"kind": "enum", "values": ["WRIT", "MAXH", "MINH", "VIEW", "BLAN"]}` | :TRACe1|2|3|4:MODE, p. 91 — WRITe|MAXHold|MINHold|VIEW|BLANk |
