# APK:data:INSTRUMENTS

The instrument library — bench panel templates by family, and the KOMAND definition tree.

| | |
|---|---|
| **Recipe** | none — data, not a container: other stacks read it or copy it in |
| **Source** | `SRC/` (this repository — https://github.com/LikeDotAudio/APK.plugin.instruments.VISA.git) — `SRC/{Counter,DAQ,DMM,Generator,LCR,Load,Oscilloscope,Power,Router,SMU,Spectrum,VNA,Distortion}` templates, `SRC/_komand/knownDevices.json`, `SRC/_datasets`, and the `apkaudio-plugin-instruments-visa` crate |
| **Used by** | `APK:plugin:VISA` (its `build.rs` walks up to `APK:data:INSTRUMENTS/SRC/_komand/knownDevices.json` and compiles it in); `APK:BareMetal/Docker/Dockerfile` copies `SRC/` to `/app/Instruments`, where the orchestrator stamps one panel per discovered instrument; `APK:web:OsApi` (`os_roots.komand_library`) |

Was `APK:BareMetal/PLUGINS/PLUGIN:instruments:VISA`. A missing library does not fail at run time — it is an empty instrument tab — and a missing `knownDevices.json` fails the VISA build.

---

*© 2026 — Written & Maintained by Anthony P. Kuzub. MIT Licence.*
