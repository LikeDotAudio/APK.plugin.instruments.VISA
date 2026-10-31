# Sources — 6060B.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## Agilent Electronic Load Family Programming Manual (Part No. 06060-90005)

Edition 3, September 1991, update April 2000 — the Programming Reference the 6060B ships with; its operating manual (5951-2826, Oct 1997) points to it — <https://xdevs.com/doc/HP_Agilent_Keysight/HP%206050A,%206051A%20Programming.pdf>

| Command | Change | Manual |
|---|---|---|
| `set/Set_Chan` | arg = `{"kind": "numeric", "min": 1}` | CHANnel, p. 41 — CHANnel[:LOAD] <NRf+> — a channel number, not an enum; on a single load CHAN? MAX returns 1 |
| `set/Set_Transient_Mode` | arg = `{"kind": "enum", "values": ["CONT", "PULS", "TOGG"]}` | TRAN:MODE, p. 70; syntax summary — CONTinuous | PULSe | TOGGle (also the 6060B Operating Manual 5951-2826, Transient Operation, pp. 24-26) |
| `set/Set_Trig_Sour` | arg = `{"kind": "enum", "values": ["BUS", "EXT", "HOLD"]}` | TRIG:SOURce, p. 74; syntax summary — BUS | EXT | HOLD | LINE | TIM, with "LINE and TIM not valid for Single Electronic Loads" — the 6060B is a single load |
| `set/Set_Inp` | drop `scpiFast` | (table only) — scpiFast repeated scpi word for word; INP is already the short form |
| `set/Set_Mode` | drop `scpiFast` | (table only) — scpiFast repeated scpi word for word |
| `set/Set_Tran_Stat` | drop `scpiFast` | (table only) — scpiFast repeated scpi word for word |
| `nab/Get_Meas_Curr` | returns = `{"count": 1, "type": "NR3", "unit": "A"}` | MEASure, p. 51 — MEASure:CURRent[:DC]? returns <NR3> amperes (9.9E+37 when out of range) |
| `nab/Get_Meas_Pow` | returns = `{"count": 1, "type": "NR3", "unit": "W"}` | MEASure, p. 51 — MEASure:POWer[:DC]? returns <NR3> watts |
| `nab/Get_Meas_Volt` | returns = `{"count": 1, "type": "NR3", "unit": "V"}` | MEASure, p. 51 — MEASure:VOLTage[:DC]? returns <NR3> volts |

### Not confirmed (left as is)

- `nab/Get_Meas_All` — searched: 06060-90005 MEASure p. 51 and the syntax summary list only MEAS:CURR?, MEAS:POW?, MEAS:VOLT? — no MEAS:ALL? exists, so there is no return shape to give it (the entry was authored from a panel literal; removing it is the owner's call)

## Retired (owner decision, 2026-10-31)

The manual shows these commands do not exist. Each entry stays in the table with `"retired": true` and its citation in `retired_because`; KOMAND never sends it, check-tables skips it, and it still counts toward the commands floor.

- `nab/Get_Meas_All` — Agilent Electronic Load Family Programming Manual 06060-90005 p. 51 (https://xdevs.com/doc/HP_Agilent_Keysight/HP%206050A,%206051A%20Programming.pdf): MEASure has CURRent?, POWer?, VOLTage? only — no MEAS:ALL?
