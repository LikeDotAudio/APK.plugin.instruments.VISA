# Sources — 54641D.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## SCPI short form of the table's own long form (54641D)

SCPI-99 Vol 1 §6.2.1 abbreviation rule; the keyword as written in the Agilent InfiniiVision 6000 Series Programmer's Guide, :MARKer:X1Position, pp. 309-310 — <https://www.cfd.rit.edu/products/manuals/Agilent/oscilloscopes/6000_series_prog_guide.pdf>

| Command | Change | Manual |
|---|---|---|
| `set/Set_X1` | scpiFast = `"MARK:X1P <pos>"` | MARKer:X1Position — the short form is the capitals, X1P |
| `set/Set_X2` | scpiFast = `"MARK:X2P <pos>"` | MARKer:X2Position — the short form is the capitals, X2P |
| `set/Set_Y1` | scpiFast = `"MARK:Y1P <lev>"` | MARKer:Y1Position — the short form is the capitals, Y1P |
| `set/Set_Y2` | scpiFast = `"MARK:Y2P <lev>"` | MARKer:Y2Position — the short form is the capitals, Y2P |

### Not confirmed (left as is)

- `set/Set_Acquire_Mode` — searched: the 54641D's own manual — Keysight "54620/40-series Oscilloscopes Programmer's Guide" (asset 9018-40679) and the "54620/40-series Programmer's Reference" help file (9018-18242) — is served only behind Keysight's download form, which refused automated fetches; no mirror (xdevs.com, manualmachine, manualslib, archive.org) carries it. The successor Agilent InfiniiVision 6000 Series Programmer's Guide (2005-2010, https://www.cfd.rit.edu/products/manuals/Agilent/oscilloscopes/6000_series_prog_guide.pdf, pp. 43-46 "Command Differences From 54620/54640") documents the same node, but its value lists carry 6000-only options (SBUS, BUS, EITHer/ALTernate, SEGMented, I2S…), so it does not confirm the 54641D's set
- `set/Set_Acquire_Mode_AVERage` — searched: as above (54641D manual not obtainable)
- `set/Set_Acquire_Mode_HRESolution` — searched: as above (54641D manual not obtainable)
- `set/Set_Acquire_Mode_NORMal` — searched: as above (54641D manual not obtainable)
- `set/Set_Acquire_Mode_PEAK` — searched: as above (54641D manual not obtainable)
- `set/Set_Acquire_Type` — searched: as above (54641D manual not obtainable)
- `set/CH1_Coupling` — searched: as above (54641D manual not obtainable)
- `set/Set_Channel_Coupling` — searched: as above (54641D manual not obtainable)
- `set/CH2_Coupling` — searched: as above (54641D manual not obtainable)
- `set/Set_Coupling` — searched: as above (54641D manual not obtainable)
- `set/Set_Impedance` — searched: as above (54641D manual not obtainable)
- `set/Set_Display_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_External_Impedance` — searched: as above (54641D manual not obtainable)
- `set/Set_External_Units` — searched: as above (54641D manual not obtainable)
- `set/Set_Function_Operation` — searched: as above (54641D manual not obtainable)
- `set/Set_Operation` — searched: as above (54641D manual not obtainable)
- `set/Set_Function_Reference` — searched: as above (54641D manual not obtainable)
- `set/Set_Source1` — searched: as above (54641D manual not obtainable)
- `set/Set_Source2` — searched: as above (54641D manual not obtainable)
- `set/Set_Window_FLATtop` — searched: as above (54641D manual not obtainable)
- `set/Set_Window_HANNing` — searched: as above (54641D manual not obtainable)
- `set/Set_Window_RECTangular` — searched: as above (54641D manual not obtainable)
- `set/Set_Hardcopy_Format` — searched: as above (54641D manual not obtainable)
- `set/Set_Marker_Mode` — searched: as above (54641D manual not obtainable)
- `set/Set_Measure_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_Mode` — searched: as above (54641D manual not obtainable)
- `set/Set_Reference` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Can_Pattern_Id_Mode` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Can_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_Edge_Slope` — searched: as above (54641D manual not obtainable)
- `set/Set_Edge_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_Edge_Source_CH1` — searched: as above (54641D manual not obtainable)
- `set/Set_Edge_Source_CH2` — searched: as above (54641D manual not obtainable)
- `set/Set_Edge_Source_EXT` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Glitch_Polarity` — searched: as above (54641D manual not obtainable)
- `set/Set_Glitch_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Lin_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Mode` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Spi_Clock_Slope` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Sweep` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Tv_Mode` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Tv_Polarity` — searched: as above (54641D manual not obtainable)
- `set/Set_Trigger_Tv_Source` — searched: as above (54641D manual not obtainable)
- `set/Set_Waveform_Format` — searched: as above (54641D manual not obtainable)
- `set/Set_Waveform_Source` — searched: as above (54641D manual not obtainable)
- `rig/Setup_Trigger_Edge` — searched: as above (54641D manual not obtainable)
