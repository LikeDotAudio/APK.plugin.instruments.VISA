<!-- BEGIN GENERATED — apkaudio-komand build-trees -->

# Router/3235 — command tree

Generated from the `.komand` table by `apkaudio-komand build-trees`. Edit the table, not this file.

**9 commands** — SET 2 · RIG 0 · NAB 2 · DO 5 · 2 unverified (22%)

`SET` one argument · `RIG` several applied together · `NAB` a query · `DO` a parameterless action. **†** marks a command swept out of a manual and never sent to the instrument.

## Tree

- `CLOSE` — **SET** `Close_Channels` · `<channel_list>` · args: `channel_list` · string
- `OPEN` — **SET** `Open_Channels` · `<channel_list>` · args: `channel_list` · string
- `CLOSE?` — **NAB** `Query_Channel_State` · `<chan>` · per-instance: `chan` · → 1 value · †
- `ID?` — **NAB** `Query_Slot_ID` · `<slot>` · per-instance: `slot` · → 1 value · †
- `CRESET` — **DO** `Card_Reset` · `<slot>` · per-instance: `slot`
- `CLR` — **DO** `Clear_State`
- `OPEN` — **DO** `Open_All` · `000-999`<br>Open every relay in the frame — nothing connected to anything.
- `RESET` — **DO** `Reset_Device`<br>Reset System
- `SELECT` — **DO** `Select_Channel` · `<chan>` · per-instance: `chan`

<!-- END GENERATED -->
