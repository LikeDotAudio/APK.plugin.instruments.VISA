# Architecture — INSTRUMENTS

← [Wiki home](../README.md)

The instrument library: bench panel templates by family, plus the KOMAND definition tree. Data, read in place by tools in a checkout and copied into images at build time. 13 families, 181 models, 16 with a `.komand` command table (3 771 commands).

## Layout

```
manifest.json                     every family's tab (and port lane) and pre-built bank groups
INSTRUMENT.<Family>/
  gui/<Family>.json               the panel, stamped once per discovered device
  gui/<Family>_N.json             the repeating block (if any)
  gui/<Family>.cad.json .probe.json .dxf
  <Model>/<Model>.gui             per-model GUI
  <Model>/<Model>.api.json        generated API spec (service = inbound, transport = outbound)
  <Model>/<Model>.komand          command table (16 models)
  <Model>/commands_tree.md        generated SCPI tree of that table
_komand/
  knownDevices.json               *IDN? catalogue; compiled into PLUGIN.VISA through the crate below
  Cargo.toml, known_devices.rs    apkaudio-known-devices: the catalogue as KNOWN_DEVICES_JSON
  ports.json                      generated port allocation
  CommandList.csv/.xlsx           generated flat list of every command
  generate_device_apis.py         writes every <Model>.api.json and ports.json (--check)
  sort_komands.py                 orders each table's verb buckets (--check)
  komands.cad.json, komands.dxf, monitor.json
_datasets/                        Instrument functions.csv/.xlsx, spectrum_presets.json
SRC/                              stub crate apkaudio-plugin-instruments-visa (DISCOVERY.Engine/SRC workspace)
```

## Who reads it

| Reader | How | What |
|---|---|---|
| `AUDIO.komand` agent | `KOMAND_REPO_PATH=/app/Instruments` in `Node-BareMetal`, or walks up to the folder holding `_komand/` | `.komand` tables → SCPI |
| `AUDIO.komand` tools | same | generate/check `CommandList.*`, `commands_tree.md`, `knownDevices.json` links |
| BareMetal orchestrator (VISA hunter) | `/app/Instruments`, `family_directory` in `NODE.BareMetal/SRC/Core/ORCHESTRATOR:hunter:VISA/src/instruments/library.rs` | stamps one panel per discovered instrument |
| `PLUGIN.VISA` | the `apkaudio-known-devices` crate (`_komand/Cargo.toml`), by git rev from this repository; patched to the local folder in the monorepo | compiled-in identification table |
| `WEB.OsApi` | `/srv/portal/Instruments`, `os_roots.komand_library()` | the instrument page and `<Model>.api.json` |

## Working on it

```bash
python3 _komand/generate_device_apis.py   # after adding a model or table; rewrites api.json + ports.json
python3 _komand/sort_komands.py           # order the verb buckets (--check to verify)
cd ../AUDIO.komand
cargo run -- check-tables                 # validate every table
cargo run -- build-list                   # CommandList.csv/.xlsx
cargo run -- build-trees                  # every commands_tree.md
cargo run -- build-links                  # knownDevices.json → tables
```

Inserting a model renumbers the later models' ports in its family; review the `ports.json` diff.
