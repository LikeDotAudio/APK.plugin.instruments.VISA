# Sources — DS1104Z.komand

Every change to this table that a vendor manual confirms, with where the manual says it (AUDIO.komand `check-tables --strict` research, 2026-10-31). A finding no manual confirmed is listed under *Not confirmed* with what was searched, and the table is left as it was.

## RIGOL MSO1000Z/DS1000Z Series Digital Oscilloscope Programming Guide

Dec. 2015 — <https://www.batronix.com/files/Rigol/Oszilloskope/_DS&MSO1000Z/MSO_DS1000Z_ProgrammingGuide_EN.pdf>

| Command | Change | Manual |
|---|---|---|
| `set/Set_Config_Format` | arg = `{"kind": "bool", "values": ["OFF", "ON"]}` | :DECoder<n>:CONFig:FORMat, p. 2-42 — <bool> {{1|ON}|{0|OFF}} — a switch, not an enum |
| `set/Set_Mod_Type` | arg = `{"kind": "enum", "values": ["AM", "FM"], "default": "AM"}` | [:SOURce[<n>]]:MOD:TYPe, p. 2-136 — <type> {AM|FM} |
| `set/Set_Output_Impedance` | arg = `{"kind": "enum", "values": ["OMEG", "FIFT"], "default": "OMEG"}` | [:SOURce[<n>]]:OUTPut[<n>]:IMPedance, p. 2-131 — <impedance> {OMEG|FIFTy} (OMEG = high-Z, FIFTy = 50 Ω) |
| `set/Set_Parallel_Polarity` | arg = `{"kind": "enum", "values": ["NEG", "POS"], "default": "POS"}`; description = `"Set or query the data polarity of parallel decoding"` | :DECoder<n>:PARallel:POLarity, p. 2-59 — <pol> {NEGative|POSitive} |
| `set/Set_Parallel_Source` | arg = `{"kind": "enum", "values": ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13", "D14", "D15", "CHAN1", "CHAN2", "CHAN3", "CHAN4"]}`; description = `"Set or query the channel source of the data bit currently selected (parallel decoding)"` | :DECoder<n>:PARallel:SOURce, p. 2-58 — <src> {D0…D15|CHANnel1…CHANnel4} |
| `set/Set_Spi_Mode` | arg = `{"kind": "enum", "values": ["CS", "TIM"], "default": "TIM"}`; description = `"Set or query the frame synchronization mode of SPI decoding"` | :DECoder<n>:SPI:MODE, p. 2-53 — <CsTmo> {CS|TIMeout} |
| `set/Set_Spi_Polarity` | arg = `{"kind": "enum", "values": ["NEG", "POS"], "default": "POS"}`; description = `"Set or query the polarity of the SDA data line in SPI decoding"` | :DECoder<n>:SPI:POLarity, p. 2-54 — <pol> {NEGative|POSitive} |
| `set/Set_Spi_Select` | arg = `{"kind": "enum", "values": ["NCS", "CS"], "default": "NCS"}`; description = `"Set or query the CS polarity in SPI decoding"` | :DECoder<n>:SPI:SELect, p. 2-52 — <CsNcs> {NCS|CS} |
| `set/Set_Threshold_Channel` | arg = `{"kind": "numeric", "unit": "V"}` | :DECoder<n>:THREshold:CHANnel1…4, p. 2-40 — <thre> is Real, (-4 × VerticalScale − VerticalOffset) to (4 × VerticalScale − VerticalOffset) — a level, not an enum |
| `set/Set_Trigger_Delay_Type` | arg = `{"kind": "enum", "values": ["GRE", "LESS", "GLES", "GOUT"], "default": "GRE"}`; description = `"Set or query the delay type in delay trigger"` | :TRIGger:DELay:TYPe, p. 2-194 — <type> {GREater|LESS|GLESs|GOUT} |
| `set/Set_Uart_Polarity` | arg = `{"kind": "enum", "values": ["NEG", "POS"], "default": "POS"}`; description = `"Set or query the polarity of RS232 decoding"` | :DECoder<n>:UART:POLarity, p. 2-45 — <pol> {NEGative|POSitive} |

### Short forms (no table change)

`:TRIGger:DURATion…`, `:SYSTem:OPTion:UNINSTall`, `:CURSor:MANual:IXDELta?` — their `scpiFast` (`DURAT`, `UNINST`, `IXDEL`) is right: "If abbreviation is used, all the capital letters in the command must be written completely" (p. 1-6, *Command Abbreviation*). The checker now reads the short form off the long form's capitals instead of truncating to four letters (AUDIO.komand `fast_is_short_form`). `:TRIGger:DELay:SLOPA` / `SLOPB` are two nodes (p. 2-192 ff.), no longer reported as an alias.
