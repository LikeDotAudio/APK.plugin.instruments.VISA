# Sources — 33210A.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## Agilent 33210A 10 MHz Function/Arbitrary Waveform Generator User's Guide (33210-90001)

Edition 1, August 2008, Chapter 3 Amplitude Modulation (AM) — <https://engineering.purdue.edu/~dionysis/EE452/Lab3/Lab3_Supporting_Materials/33210A_Function_Generator_Users_Guide.pdf>

| Command | Change | Manual |
|---|---|---|
| `rig/Setup_AM` | arg = `{"kind": "multi", "parameters": {"shape": {"kind": "enum", "values": ["SIN", "SQU", "RAMP", "NRAM", "TRI", "NOIS", "USER"], "default": "SIN"}, "freq": {"kind": "numeric", "unit": "Hz", "min": 0.002, "max": 20000}, "depth": {"kind": "numeric", "unit": "%", "min": 0, "max": 120}}}` | AM:INTernal:FUNCtion and AM:INTernal:FREQuency pp. 74-75; AM:DEPTh p. 75 — shape {SINusoid|SQUare|RAMP|NRAMp|TRIangle|NOISe|USER}; modulating frequency (internal) 2 mHz to 20 kHz, default 100 Hz; depth 0% to 120%, default 100% |
