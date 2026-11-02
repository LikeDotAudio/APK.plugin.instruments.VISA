<!-- BEGIN GENERATED — apkaudio-komand build-trees -->

# TestSet/E5515C — command tree

Generated from the `.komand` table by `apkaudio-komand build-trees`. Edit the table, not this file.

**36 commands** — SET 7 · RIG 2 · NAB 22 · DO 5 · 36 unverified (100%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **RIG** `Configure_Audio_Loopback` · args: `state`, `delay` · †<br>Configure speech echo loopback and delay
  - `:CALL:AUDio:SPEech:ECHO:STATe <state>;:CALL:AUDio:SPEech:ECHO:DELay <delay>`
- **RIG** `Configure_Cell` · args: `band`, `channel`, `power` · †<br>Configure cell band, channel, and RF power together
  - `:CALL:BAND <band>;:CALL:CHANnel <channel>;:CALL:POWer <power>`

## Tree

- **`CALL`**
  - `BAND` — **SET** `Set_Call_Band` · `<value>` · args: `value` · †<br>Set cellular operating band
  - `CHANnel` — **SET** `Set_Call_Channel` · `<value>` · args: `value` · †<br>Set cellular channel ARFCN
  - `POWer` — **SET** `Set_Cell_Power` · `<value>` · args: `value` · †<br>Set RF cell power level in dBm
  - `BAND?` — **NAB** `Get_Call_Band` · → CRD · †<br>Query operating band
  - `CHANnel?` — **NAB** `Get_Call_Channel` · → NR1 · †<br>Query current ARFCN channel
  - `STATUS?` — **NAB** `Get_Call_Status` · → CRD · †<br>Query call processing status
  - `POWer?` — **NAB** `Get_Cell_Power` · → NR3 · †<br>Query RF cell power level
  - `PCONnection` — **DO** `Connect_Call` · †<br>Establish cellular call connection
  - `END` — **DO** `End_Call` · †<br>End active cellular call
  - **`AUDio`**
    - **`SPEech`**
      - **`ECHO`**
        - `STATe` — **SET** `Set_Speech_Echo_State` · `<value>` · args: `value` · †<br>Set speech loopback echo state
        - `STATe?` — **NAB** `Get_Speech_Echo_State` · → BOOL · †<br>Query speech loopback echo state
  - **`PCONnection`**
    - `STATe?` — **NAB** `Get_Connection_State` · → CRD · †<br>Query packet data connection state
- **`MEASure`**
  - `BER?` — **NAB** `Get_Ber` · → NR3 · †<br>Measure Bit Error Rate
  - `EVM?` — **NAB** `Get_Evm` · → NR3 · †<br>Measure Error Vector Magnitude
  - `FER?` — **NAB** `Get_Fer` · → NR3 · †<br>Measure Frame Error Rate
  - `FERRor?` — **NAB** `Get_Frequency_Error` · → NR3 · †<br>Measure carrier frequency error
  - `OBWidth?` — **NAB** `Get_Occupied_Bandwidth` · → NR3 · †<br>Measure occupied bandwidth
  - `TXPower?` — **NAB** `Get_Tx_Power` · → NR3 · †<br>Measure transmitter RF power
  - **`AFANalyzer`**
    - `FREQuency?` — **NAB** `Get_Audio_Frequency` · → NR3 · †<br>Measure audio tone frequency
    - `DISTortion?` — **NAB** `Get_Distortion` · → NR3 · †<br>Measure audio THD / THD+N distortion
    - `SINAd?` — **NAB** `Get_Sinad` · → NR3 · †<br>Measure audio SINAD in dB
    - **`VOLTage`**
      - `AC?` — **NAB** `Get_Audio_Ac_Voltage` · → NR3 · †<br>Measure audio RMS AC voltage
      - `DC?` — **NAB** `Get_Audio_Dc_Voltage` · → NR3 · †<br>Measure audio DC voltage
- **`SYSTem`**
  - `ERRor?` — **NAB** `Get_System_Error` · → CRD · †<br>Query system error queue
  - **`DISPlay`**
    - `UPDate` — **SET** `Set_Display_Update` · `<value>` · args: `value` · †<br>Set screen update / blanking state to maximize bus execution speed
    - `UPDate?` — **NAB** `Get_Display_Update` · → BOOL · †<br>Query screen update state

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Clear_Status` · †<br>Clear status registers and error queue
- `*IDN?` — **NAB** `Get_Idn` · → CRD · †<br>Identification query
- `*OPC?` — **NAB** `Get_Opc` · → BOOL · †<br>Operation complete query
- `*STB?` — **NAB** `Get_Status_Byte` · → NR1 · †<br>Read status byte query
- `*RST` — **DO** `Reset` · †<br>Reset instrument to factory defaults
- `*ESE <value>` — **SET** `Set_Ese` · `<value>` · args: `value` · †<br>Set Standard Event Status Enable
- `*SRE <value>` — **SET** `Set_Sre` · `<value>` · args: `value` · †<br>Set Service Request Enable
- `*WAI` — **DO** `Wait_To_Continue` · †<br>Wait for pending operations to complete

<!-- END GENERATED -->
