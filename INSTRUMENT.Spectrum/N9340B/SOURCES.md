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

## Not confirmed — undocumented `:DEBug` commands (2026-10-31)

Not in N9340-90010. Read out of the vendor's **N9340 PC Software** (`N9340 PC Software.exe`, .NET, decompiled with ilspycmd): `Agilent.N9340B.VISA.SCPI.DefSCPI` (the `Def:` commands: `:DEBug:REMote STATE / TRACe1-4 / PTRACe / PMARker / DMARker`), `Agilent.N9340B.VISA.FILESCPI` (`FILe`, `NEXT`, `CFILe:Cancel / ReadFILe / ReadFILe:Next / WriteFile / WriteFile? / DelFile / DelFile?`), `cMonitor` (the frame decoders) and `cFrmUpgrade` (`DEBUG:FTP?`, `DEBUG:FTP 1`, `DEB:FTP 0`, `DEBUG:NFL:AVA?`). The vendor's `Std:`/`Def:` prefixes are its own queue tags and are never sent. Cross-checked against the owner's `n9340_fasttrace.py`.

Every `Def:` command and the file commands answer with ONE binary **HOYI frame** although they carry no `?` — those nabs declare `"returns": {"type": "HOYI"}` (KOMAND's validator accepts a nab without `?` for that type), and PLUGIN.VISA reads them through `reply_without_query` in its config.ini and frames them by length (`instrument::hoyi_len`: 29 + u16 LE @6 + 1 bytes), never at a newline. The frame layouts are in each entry's `notes`. All are `unverified` and `model_only` (the Spectrum models inheriting this table do not get them). Not probed: CN03480580 at 44.44.44.66 did not answer on 2026-10-31.
