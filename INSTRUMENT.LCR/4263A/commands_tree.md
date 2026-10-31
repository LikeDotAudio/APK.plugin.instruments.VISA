<!-- BEGIN GENERATED — apkaudio-komand build-trees -->

# LCR/4263A — command tree

Generated from the `.komand` table by `apkaudio-komand build-trees`. Edit the table, not this file.

**39 commands** — SET 27 · RIG 0 · NAB 6 · DO 6 · 39 unverified (100%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Tree

- `CURR` — **SET** `Set_Curr` · `<value>` · numeric (A) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
- `INP` — **SET** `Set_Inp` · `<state>` · bool: `OFF` | `ON` · per-instance: `state` · †<br>Authored from a panel literal in LCR.json; never executed before.
- `MODE` — **SET** `Set_Mode` · `<value>` · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
- `RES` — **SET** `Set_Res` · `<value>` · numeric (Ohm) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
- `VOLT` — **SET** `Set_Volt` · `<value>` · numeric (V) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
- `FETCh?` — **NAB** `Fetch_Existing` · → 1 value · †<br>Retrieves the most recent measurement data.
- `MEASure?` — **NAB** `Measure` · → 1 value · †<br>Executes a complete measurement and retrieves data.
- `READ?` — **NAB** `Read_Measurement` · → 1 value · †<br>Triggers a measurement and retrieves the results.
- `TRIGger` — **DO** `Trigger_Immediate` · †<br>Manually triggers a measurement.
- **`CALCulate`**
  - **`LIMit`**
    - `LOWer` — **SET** `Limit_Lower` · `<limit>` · args: `limit` · numeric · †<br>Sets the lower limit for the comparator.
    - `STATe` — **SET** `Limit_State` · `<state>` · args: `state` · bool: `OFF` | `ON` · †<br>Enables or disables the comparator function.
    - `UPPer` — **SET** `Limit_Upper` · `<limit>` · args: `limit` · numeric · †<br>Sets the higher limit for the comparator.
- **`CURR`**
  - `LEV` — **SET** `Set_Curr_Lev` · `<value>` · numeric (A) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
  - `SLEW` — **SET** `Set_Curr_Slew` · `<value>` · numeric (A/s) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
  - `TLEV` — **SET** `Set_Curr_Tlev` · `<value>` · numeric (A) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
- **`DISPlay`**
  - `STATe` — **SET** `Display_State` · `<state>` · args: `state` · bool: `OFF` | `ON` · †<br>Turns the display ON or OFF.
- **`SENSe`**
  - `FUNCtion` — **SET** `Measurement_Function` · `<function>` · args: `function` · enum · †<br>Selects measurement parameters (e.g., CP-D, LS-Q).
  - `FREQuency` — **SET** `Set_Test_Frequency` · `<freq>` · args: `freq` · numeric (Hz) · †<br>Sets the test signal frequency (100, 1k, 10k, 100k Hz).
  - **`AVERage`**
    - `COUNt` — **SET** `Average_Count` · `<count>` · args: `count` · integer · †<br>Sets the number of measurement averages (1 to 256).
  - **`CORRection`**
    - `OPEN` — **DO** `Correction_Open` · †<br>Executes the OPEN correction.
    - `SHORt` — **DO** `Correction_Short` · †<br>Executes the SHORT correction.
  - **`CURRent`**
    - `RANGe` — **SET** `Current_Range` · `<range>` · args: `range` · numeric · †<br>Sets the current measurement range.
  - **`VOLTage`**
    - **`RANGe`**
      - `AUTO` — **SET** `Voltage_Range_Auto` · `<state>` · args: `state` · bool: `OFF` | `ON` · †<br>Enables or disables auto-ranging.
- **`SOURce`**
  - `VOLTage` — **SET** `Set_Test_Level` · `<level>` · args: `level` · numeric (V) · †<br>Sets the test signal level (e.g., 100m, 500m, 1V).
  - **`BIAS`**
    - `STATe` — **SET** `Set_Bias_State` · `<state>` · args: `state` · bool: `OFF` | `ON` · †<br>Turns the DC bias ON or OFF.
    - `VOLTage` — **SET** `Set_Bias_Voltage` · `<volt>` · args: `volt` · numeric (V) · †<br>Sets the internal DC bias voltage level.
- **`SYSTem`**
  - `KLOCk` — **SET** `Key_Lock` · `<state>` · args: `state` · bool: `OFF` | `ON` · †<br>Locks or unlocks the front-panel keys.
  - `ERRor?` — **NAB** `Get_Error_Queue` · → NR2 · †<br>Queries the next entry in the error queue.
  - **`BEEPer`**
    - `STATe` — **SET** `Set_Beeper` · `<state>` · args: `state` · bool: `OFF` | `ON` · †<br>Turns the front-panel beeper ON or OFF.
- **`TRAN`**
  - `DCYC` — **SET** `Set_Tran_Dcyc` · `<value>` · numeric (%) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
  - `FREQ` — **SET** `Set_Tran_Freq` · `<value>` · numeric (Hz) · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
  - `STAT` — **SET** `Set_Tran_Stat` · `<value>` · bool: `OFF` | `ON` · per-instance: `value` · †<br>Authored from a panel literal in LCR.json; never executed before.
- **`TRIGger`**
  - `DELay` — **SET** `Trigger_Delay` · `<seconds>` · args: `seconds` · numeric (s) · †<br>Sets the delay time before measurement starts.
  - `SOURce` — **SET** `Trigger_Source` · `<source>` · args: `source` · enum · †<br>Selects trigger source (INT, MAN, EXT, or BUS).

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Clear_Status` · †<br>Clears the status byte and error queue.
- `*OPC?` — **NAB** `Get_Operation_Complete` · → NR1 · †<br>Returns '1' once all pending operations are completed.
- `*IDN?` — **NAB** `Read_IDN` · → AARD · †<br>Queries the instrument identification (Manufacturer, Model, Serial, Firmware).
- `*RST` — **DO** `Reset_Device` · †<br>Resets the unit to its factory default settings.
- `*TRG` — **DO** `Trigger_Bus` · †<br>Triggers the unit (equivalent to the Bus trigger).

<!-- END GENERATED -->
