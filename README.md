# APK:data:INSTRUMENTS

The instrument library — bench panel templates by family, and the KOMAND definition tree.

| | |
|---|---|
| **Recipe** | none — data, not a container: other stacks read it or copy it in |
| **Source** | `SRC/` (this repository — https://github.com/LikeDotAudio/APK.plugin.instruments.VISA.git) — `SRC/{Counter,DAQ,DMM,Generator,LCR,Load,Oscilloscope,Power,Router,SMU,Spectrum,VNA,Distortion}` templates, `SRC/_komand/knownDevices.json`, `SRC/_datasets`, and the `apkaudio-plugin-instruments-visa` crate |
| **Used by** | `APK:plugin:VISA` (its `build.rs` walks up to `APK:data:INSTRUMENTS/SRC/_komand/knownDevices.json` and compiles it in); `APK:BareMetal/Docker/Dockerfile` copies `SRC/` to `/app/Instruments`, where the orchestrator stamps one panel per discovered instrument; `APK:web:OsApi` (`os_roots.komand_library`) |

---

## One name per file

An instrument's API spec is **always** `<Model>.api.json` — `SMU/2410/2410.api.json`,
never `SMU/2410/api.json`. Each model folder used to carry a bare `api.json`
symlink beside the real file; 181 of them were swept on 2026-09-20 and the
generator now removes any that reappear.

The generic name was the whole problem: `SMU/2410/api.json` and
`DMM/34411A/api.json` are the same string, so an open editor tab, a grep hit and
a stack trace all stopped saying *which* instrument they meant. Nothing ever
read the symlink — `APK:web:OsApi` (`server.py`) has always opened
`f'{model}.api.json'` directly — so it bought convenience and cost identity.

---

## Instrument addresses

Every `<Model>.api.json` carries two address blocks, and they point in opposite
directions. Confusing them is the classic way to end up dialling 5025 on the
wrong side, so they are named for the direction they face:

| Block | Direction | Holds |
|---|---|---|
| `service` | **inbound** — where this API answers | `host`, `port`, the `/api/instrument/<Family>/<Model>` base path, the five verb `routes`, and a `socket` (`/ws/…`, `/ws/…/readings`, and a unix socket under `/run/apk/instruments/`) |
| `transport` | **outbound** — how this API reaches the box | VISA resource templates per interface, and the well-known SCPI socket ports: raw `5025`, HiSLIP `4880`, VXI-11 `111`, telnet `5024` |

`transport` is protocol constants, **not** an interface inventory — a 3458A has
no ethernet and its file still lists HiSLIP. What a given box actually answers
on is measured by the discovery sweep and written to the family probe file.

**The port is derived, never stored:**

```
port = 15000 + family_index * 100 + model_index
```

`family_index` is the digit in front of the class's `tab` in `manifest.json`;
`model_index` is its position in the family's sorted model list. 181 models
occupy **15000–16207** in 100-wide lanes, clear of everything the system
already holds (1883-1885, 3221, 5000/5001, 5004, 5007/5008, 5024/5025,
5101-5106, 5201, 5301-5306, 5353, 5683, 5959-5970, 8009, 8080/8081, 8100,
9000, 9001-9003).

The cost of deriving it: **inserting a model renumbers every model after it in
its family.** `_komand/ports.json` is rewritten on every run so that shift
arrives as a reviewable diff rather than a silent reassignment on the wire, and
a family overflowing its 100-slot lane fails at generation time instead of
colliding later. Both files are outputs of
`python3 _komand/generate_device_apis.py` — change the allocator, not the JSON.

Was `APK:BareMetal/PLUGINS/PLUGIN:instruments:VISA`. A missing library does not fail at run time — it is an empty instrument tab — and a missing `knownDevices.json` fails the VISA build.

---

*© 2026 — Written & Maintained by Anthony P. Kuzub. MIT Licence.*
