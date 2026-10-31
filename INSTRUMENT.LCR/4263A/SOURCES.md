# Sources — 4263A.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## Not confirmed (left as is)

- `set/Set_Mode` — searched: HP 4263A LCR Meter operation/programming manual: searched xdevs.com, manualmachine, manualslib, Keysight; only the successor 4263B's documents were found (User's Guide at xdevs.com, Operation Manual at manualmachine), which are not the 4263A's. The MEAS:ALL?/CURR?/POW?/VOLT? entries were authored from a panel literal and look like electronic-load commands, not LCR ones — nothing confirms them
- `set/Measurement_Function` — searched: as above
- `set/Trigger_Source` — searched: as above
- `nab/Get_Meas_All` — searched: as above
- `nab/Get_Meas_Curr` — searched: as above
- `nab/Get_Meas_Pow` — searched: as above
- `nab/Get_Meas_Volt` — searched: as above

## Retired (owner decision, 2026-10-31)

The manual shows these commands do not exist. Each entry stays in the table with `"retired": true` and its citation in `retired_because`; KOMAND never sends it, check-tables skips it, and it still counts toward the commands floor.

- `nab/Get_Meas_All` — Owner decision 2026-10-31: no HP 4263A manual was obtainable, and MEAS:ALL?/CURR?/POW?/VOLT? are the electronic-load measurement set (Electronic Load Family Programming Manual 06060-90005 p. 51), authored here from a panel literal — an LCR meter measures impedance, not load current/power
- `nab/Get_Meas_Curr` — Owner decision 2026-10-31: no HP 4263A manual was obtainable, and MEAS:ALL?/CURR?/POW?/VOLT? are the electronic-load measurement set (Electronic Load Family Programming Manual 06060-90005 p. 51), authored here from a panel literal — an LCR meter measures impedance, not load current/power
- `nab/Get_Meas_Pow` — Owner decision 2026-10-31: no HP 4263A manual was obtainable, and MEAS:ALL?/CURR?/POW?/VOLT? are the electronic-load measurement set (Electronic Load Family Programming Manual 06060-90005 p. 51), authored here from a panel literal — an LCR meter measures impedance, not load current/power
- `nab/Get_Meas_Volt` — Owner decision 2026-10-31: no HP 4263A manual was obtainable, and MEAS:ALL?/CURR?/POW?/VOLT? are the electronic-load measurement set (Electronic Load Family Programming Manual 06060-90005 p. 51), authored here from a panel literal — an LCR meter measures impedance, not load current/power
