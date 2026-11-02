# Sources — Virtual_TestSet

APK.audio Virtual Test Set (Synthesized RF + Audio Multi-Function Emulator).

## Architecture
- Emulates dual-domain test set functionality (Cellular RF base station + Audio precision analyzer).
- Responds to standard IEEE 488.2 queries (`*IDN?`, `*RST`, `*OPC?`).
- Provides synthetic RF telemetry (Power, BER, EVM) and Audio telemetry (Level, Frequency, THD+N, SINAD).
- Provides both raw TCP SCPI socket server and MQTT databus endpoints.
