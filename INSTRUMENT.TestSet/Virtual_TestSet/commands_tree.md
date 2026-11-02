<!-- BEGIN GENERATED — apkaudio-komand build-trees -->

# TestSet/Virtual_TestSet — command tree

Generated from the `.komand` table by `apkaudio-komand build-trees`. Edit the table, not this file.

**20 commands** — SET 3 · RIG 1 · NAB 10 · DO 6 · 0 unverified (0%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Compound commands

Several statements in one message, so they hang off no single branch. Every statement after the first carries a leading colon — without it the parser reads it relative to the previous header's path and the instrument answers `-113`.

- **RIG** `Configure_Audio_Test` · args: `freq`, `level`<br>Configure audio generator frequency and level together
  - `SOURce:AUDio:FREQuency <freq>;:SOURce:AUDio:LEVel <level>`

## Tree

- **`CALL`**
  - `STATUS?` — **NAB** `Get_Call_Status` · → CRD<br>Query cellular call connection status
  - `PCONnection` — **DO** `Connect_Call`<br>Establish cellular call connection
  - `END` — **DO** `End_Call`<br>Terminate active cellular call
- **`MEASure`**
  - `BER?` — **NAB** `Get_Ber` · → NR3<br>Measure Bit Error Rate percentage
  - `EVM?` — **NAB** `Get_Evm` · → NR3<br>Measure Error Vector Magnitude percentage
  - **`AFANalyzer`**
    - `SINAd?` — **NAB** `Get_Sinad` · → NR3<br>Measure audio SINAD ratio in dB
  - **`AUDio`**
    - `LEVel?` — **NAB** `Get_Audio_Level` · → NR3<br>Measure incoming audio voltage in Volts RMS
    - `THD?` — **NAB** `Get_Thd` · → NR3<br>Measure audio Total Harmonic Distortion plus Noise in percentage
  - **`RF`**
    - `POWer?` — **NAB** `Get_Rf_Power` · → NR3<br>Measure received RF power in dBm
- **`SOURce`**
  - **`AUDio`**
    - `FREQuency` — **SET** `Set_Audio_Freq` · `<value>` · args: `value`<br>Set audio generator frequency in Hertz
    - `LEVel` — **SET** `Set_Audio_Level` · `<value>` · args: `value`<br>Set audio generator output level in Volts RMS
    - `FREQuency?` — **NAB** `Get_Audio_Freq` · → NR3<br>Query audio generator frequency
  - **`RF`**
    - `POWer` — **SET** `Set_Rf_Power` · `<value>` · args: `value`<br>Set output RF generator power level in dBm

## Common commands (IEEE 488.2)

- `*CLS` — **DO** `Clear_Status`<br>Clear Status Command
- `*IDN?` — **NAB** `Get_Idn` · → CRD<br>Identification Query
- `*OPC?` — **NAB** `Get_Opc` · → BOOL<br>Operation Complete Query
- `*OPC` — **DO** `Operation_Complete`<br>Operation Complete Command
- `*RST` — **DO** `Reset`<br>Reset Command
- `*WAI` — **DO** `Wait_To_Continue`<br>Wait-to-Continue Command

<!-- END GENERATED -->
