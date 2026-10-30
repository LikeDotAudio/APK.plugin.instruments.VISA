# INSTRUMENTS

The instrument library — bench panel templates by family, and the KOMAND definition tree: 13 families, 181 models, 16 of them with a `<Model>.komand` command table.

| | |
|---|---|
| **Recipe** | none — data, not a container: other stacks read it or copy it in |
| **Source** | this repository (https://github.com/LikeDotAudio/APK.plugin.instruments.VISA.git) — `INSTRUMENT.{Counter,DAQ,DMM,Distortion,Generator,LCR,Load,Oscilloscope,Power,Router,SMU,Spectrum,VNA}` families (see *Layout* below), `manifest.json`, `_komand/` (`knownDevices.json`, `ports.json`, `CommandList.csv`/`.xlsx`, the generators), `_datasets/`, and in `SRC/` the `apkaudio-plugin-instruments-visa` crate — a stub binary that prints its name, a member of the `DISCOVERY.Engine/SRC` workspace |
| **Used by** | `PLUGINS/PLUGIN.VISA` (its `build.rs` finds `INSTRUMENTS/_komand/knownDevices.json` and compiles it in); `NODE.BareMetal/Docker/Dockerfile` copies this whole folder to `/app/Instruments`, where the orchestrator stamps one panel per discovered instrument and `AUDIO.komand` reads the command tables (`KOMAND_REPO_PATH=/app/Instruments`); `WEB.OsApi` (`os_roots.komand_library()`) |

---

## Layout

This is the central home of every bench instrument's GUI. One folder per
family, and the folder carries the `INSTRUMENT.` prefix:

```
INSTRUMENT.DMM/
  gui/                  the family's GUI — real files, and the only copy
    DMM.json            the instrument panel, stamped once per device
    DMM_N.json          N of the instrument — the block that repeats (if any)
    DMM.cad.json        CAD drawing definition
    DMM.probe.json      probe points
    DMM.dxf             the drawing
  34401A/               one folder per model: <Model>.gui, <Model>.komand,
  …                     <Model>.api.json
```

`Router`'s `gui/` also holds `Cards.json` (the HP 3235 port map).

**The prefix belongs to the directory and to nothing else.** The family NAME —
the device type, the MQTT topics, the `manifest.json` key, its `tab`, the port
lane and `${family}` — is always the bare `DMM`. A reader resolves a family's
folder as `INSTRUMENT.<Family>` if it exists, else `<Family>` (so a crate's
`gui/dante/` and an older tree still read), and strips a leading `INSTRUMENT.`
(or the legacy `INSTRUMENT:`) when it derives a family name from a directory
listing. Each language has one helper for that: `family_directory` in the
orchestrator (`NODE.BareMetal/SRC/Core/ORCHESTRATOR:hunter:VISA/src/instruments/library.rs`),
`family_name`/`family_directory` in `_komand/generate_device_apis.py`,
`Baremetal:Manager/node_paths.py` and `WEB.OsApi/SRC/os_roots.py`.

---

## One name per file

An instrument's API spec is **always** `<Model>.api.json` — `INSTRUMENT.SMU/2410/2410.api.json`,
never `INSTRUMENT.SMU/2410/api.json`. The family's GUI files follow the same rule:
`gui/DMM.cad.json`, never `gui/cad.json`. Each model folder used to carry a bare `api.json`
symlink beside the real file; 181 of them were swept on 2026-09-20 and the
generator now removes any that reappear.

The generic name was the whole problem: `SMU/2410/api.json` and
`DMM/34411A/api.json` are the same string, so an open editor tab, a grep hit and
a stack trace all stopped saying *which* instrument they meant. Nothing ever
read the symlink — `WEB.OsApi` (`server.py`) has always opened
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

## Generate and check

All from this folder; measured 2026-10-30.

```bash
python3 _komand/generate_device_apis.py      # every <Model>.api.json + _komand/ports.json — re-running changes nothing today
python3 _komand/sort_komands.py --check      # 0 tables out of order
# the command-table tooling lives in the KOMAND binary:
cd ../AUDIO.komand && KOMAND_REPO_PATH=../INSTRUMENTS cargo run -- check-tables      # 3 771 commands, 16 models
cd ../DISCOVERY.Engine/SRC && cargo check -p apkaudio-plugin-instruments-visa         # the stub crate builds
```

Two generated reports are behind the tree today: `KOMAND_REPO_PATH=../INSTRUMENTS cargo run -- build-list --check` (in `AUDIO.komand`) finds `_komand/CommandList.csv` stale — its `File` column still names the pre-rename `DMM/34401A/…` paths — and `build-trees --check` reports all 16 `commands_tree.md` missing (none is tracked).

`manifest.json` says `check.sh binding` fails when the families and the manifest diverge; no `check.sh` is in the tree today.

## Philosophy

- **Data, not a container.** No `Docker/`; images copy the folder in (`NODE.BareMetal/Docker/Dockerfile`, `COPY ["PODS/POD.THICK/INSTRUMENTS", "./Instruments"]`).
- **The prefix belongs to the directory.** `INSTRUMENT.DMM` is a folder; `DMM` is the family everywhere else, and every reader has one helper to translate (`_komand/generate_device_apis.py`, `family_name` / `family_directory`).
- **One name per file.** `<Model>.api.json`, never `api.json`, so a path names its instrument; the generator removes stray bare names (`_komand/generate_device_apis.py`, module doc).
- **Derive, don't store — and show the cost.** Ports are computed from the manifest `tab` and model order; `ports.json` is rewritten each run so a renumbering is a reviewable diff, and a full lane fails at generation (`_komand/generate_device_apis.py`, lines 80+).
- **Reports are outputs.** `CommandList.csv`, `ports.json` and every `<Model>.api.json` are generated from the tables and the manifest — "change the allocator, not the JSON".
- **Every class is declared.** A family folder with no `manifest.json` entry is an error, not a quiet gap (`manifest.json`, `_note.every_class_needs_an_entry`).

Plans for this repo live in the house roadmap, `Documentation/🛣Roadmap/roadmap.htm` in APK.audio.

---

*© 2026 — Written & Maintained by Anthony P. Kuzub. MIT Licence.*
