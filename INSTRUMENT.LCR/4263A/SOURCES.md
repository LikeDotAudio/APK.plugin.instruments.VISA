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
