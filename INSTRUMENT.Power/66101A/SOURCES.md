# Sources — 66101A.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## Programming Guide for HP Series 66lxxA MPS Power Modules (HP Part No. 5959-3362)

September 1997 — Chapter 3, Language Dictionary; it states the commands work the same in every 6610xA module — <https://xdevs.com/doc/HP_Agilent_Keysight/661xxA_programming.pdf>

| Command | Change | Manual |
|---|---|---|
| `set/Set_Output_Dfi_Source` | arg = `{"kind": "enum", "values": ["LINK"], "default": "LINK"}` | OUTP:DFI:SOUR, p. 40 — Parameters LINK — "The only available source is LINK" |
| `set/Set_Output_Relay_Polarity` | arg = `{"kind": "enum", "values": ["NORM", "REV"], "default": "NORM"}` | OUTP:REL:POL, p. 41 — Parameters NORMal | REVerse, *RST NORM |
| `set/Set_Output_Ttltrg_Source` | arg = `{"kind": "enum", "values": ["BUS", "EXT", "LINK", "HOLD"], "default": "BUS"}` | OUTP:TTLT:SOUR, p. 42 — Parameters BUS | EXTernal | LINK | HOLD, *RST BUS |
| `set/Set_Source_Current_Mode` | arg = `{"kind": "enum", "values": ["FIX", "LIST"], "default": "FIX"}` | CURR:MODE, p. 35 — Parameters FIXed | LIST, *RST FIX |
| `set/Set_Source_Voltage_Mode` | arg = `{"kind": "enum", "values": ["FIX", "LIST"], "default": "FIX"}` | VOLT:MODE, p. 48 — Parameters FIXed | LIST, *RST FIX |
| `set/Set_Trigger_Source` | arg = `{"kind": "enum", "values": ["BUS", "EXT", "HOLD", "LINK", "TTLT"], "default": "BUS"}` | TRIG:SOUR, p. 47 — TRIGger[:STARt]:SOURce Parameters BUS | EXT | HOLD | LINK | TTLT, *RST BUS |
| `set/Set_Trigger_Start_Source` | arg = `{"kind": "enum", "values": ["BUS", "EXT", "HOLD", "LINK", "TTLT"], "default": "BUS"}` | TRIG:SOUR, p. 47 — the same node, TRIGger[:STARt]:SOURce |

### Not confirmed (left as is)

- `set/Set_Status_Operation` — searched: 5959-3362 Status subsystem pp. 43–44: STATus:OPERation[:EVENt]? is query-only and the settable registers are STAT:OPER:ENAB/NTR/PTR <NRf> (0–32727); no `STAT:OPER <value>` set command exists, so there is no choice list to give it. Removing or re-pointing the entry is the owner's call (the commands floor)
- `set/Set_Voltage_Alc_Source` — searched: 5959-3362 VOLT:SENS:SOUR?, p. 49: the remote-sense switch is READ ("This command reads the state…"), query-only, returns EXTernal | INTernal; VOLT:ALC:SOUR is its SCPI alias. No set form, so no settable choice list
- `set/Set_Voltage_Sense_Source` — searched: as Set_Voltage_Alc_Source: query-only [SOURce]:VOLTage:SENSe:SOURce?, p. 49
