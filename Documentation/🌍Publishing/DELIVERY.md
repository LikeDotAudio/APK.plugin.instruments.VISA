# Delivery — INSTRUMENTS

← [Wiki home](../README.md)

No build of its own: it lands by being copied into images. Each copy is a snapshot, so an edit here reaches a running bench only after the image that bakes it is rebuilt.

| Image (stack) | Copy | Rebuild with |
|---|---|---|
| `node-baremetal:local` (`NODE.BareMetal`) | `NODE.BareMetal/Docker/Dockerfile` line 253 → `/app/Instruments` (KOMAND agent, orchestrator panels); line 74 for the VISA build | `PODS/POD.manager/MANAGER.Docktor/K8/up-stack.sh NODE.BareMetal` |
| OsApi (`WEB.OsApi`) | `WEB.OsApi/Docker/Dockerfile` line 35 → `/srv/portal/Instruments` (the instrument page) | `up-stack.sh WEB.OsApi` |
| Discovery Engine (`DISCOVERY.Engine`) | `DISCOVERY.Engine/Docker/Dockerfile` line 62, for `knownDevices.json` at build time | `up-stack.sh DISCOVERY.Engine` |
| Broker (`DATABUS.Broker.MQTT`) | `DATABUS.Broker.MQTT/Docker/Dockerfile` line 62, as a member of the Rust workspace that image builds | the broker is protected: DockTor never stops or removes it, so rebuild it deliberately |

## Checks

```bash
python3 _komand/sort_komands.py --check                 # 0 tables out of order
python3 _komand/generate_device_apis.py --check         # 0 file(s) out of date; manifest and folders agree
../../../.apk.scripts/check.sh instruments              # both Python checks above, as a root lane
cd ../AUDIO.komand && cargo run -- check-tables
cargo run -- build-list --check && cargo run -- build-trees --check && cargo run -- build-links --check
```

`python3 .apk.scripts/smoke.py PODS/POD.THICK/INSTRUMENTS` (root) writes [SMOKE.md](../%F0%9F%A7%A9Manual%20and%20Artifacts/SMOKE.md); its only check is that the repo is pushed.

## Not automated

- No CI in this repo (the root's rule); the one local command is `_komand/check.sh`. No pre-build gate runs any check above. The root `check.sh` runs the two Python checks in its default lanes, but only when someone runs it; the `AUDIO.komand` cargo checks are run by hand.
- Images are rebuilt by hand; nothing rebuilds them on a push here.
- No live URL of its own; the library surfaces through the OsApi instrument page on the bench.

## Delivered from the 2026-10-30 audit

- **JSON Schemas, enforced, one check command** — `_komand/schemas/` (`gui`, `komand`+`command`, `api`, `manifest`, `families`, `baseline`), validated by the dependency-free `_komand/schema_check.py` and by `generate_device_apis.py --check` (384 files, 0 problems; a typo'd key, a missing field or a wrong type is refused — proved on a scratch copy). `_komand/check.sh` runs both `--check`s, `test_instruments.py` (7 tests) and `cargo test` in `_komand/`; it passes. No workflow added (root rule). The root `check.sh instruments` lane already runs the generator `--check`, so it now covers the schemas too.
- **Catalogue fields single-checked** — `.gui` is the source for `manufacturer`/`type`/`notes`; `--check` fails naming every field where `knownDevices.json` (the catalogue PLUGIN.VISA compiles in) says otherwise (`catalogue_disagreements`). Today 0 of 181 disagree. Kept two copies by design: `knownDevices.json` is the crate PLUGIN.VISA links by git rev, so the fields must ride in it; the check makes the two one truth.
- **A broken `.gui` fails loudly** — `generate_device_api` raises `BrokenGui` naming the file (was `except Exception: pass`); proved on a scratch copy (exit 1, file and parse error named).
- **Family resolver as data** — `families.json` (family → folder, `prefix`, `legacy_prefixes`); `family_directory` reads it; `--check` fails when it and the folders disagree. The other three readers (NODE.BareMetal `instruments/library.rs` + `Baremetal:Manager/node_paths.py`, WEB.OsApi `os_roots.py`) are asked to read it (handoffs filed).
- **Baselines and donors are data** — `BASELINE_COMMANDS` (~950 lines) and `PRIMARY_DONOR_MODELS` moved to `_komand/baselines/<Family>.json` and `donors.json` (outside the family folders, so no panel/table reader picks them up); `generate_device_apis.py` is 1535 → ~600 lines and every generated spec is byte-identical (`--check`: 0 of 181 out of date). `--check` also refuses a donor that is not an authored model.
- **INSTRUMENTS baked into images** — Kept by design (house rule: OS/ and INSTRUMENTS baked into images; OsApi serves the image copy). Part of the plugin image (VISA's catalogue), the NODE.BareMetal image (komand tables) and WEB.OsApi (instrument page): those images need a rebuild after an edit here.
- **A removed model's port is retired by name** — `_komand/retired_ports.json`; `generate_device_apis.py --check` fails when a Family/Model in the previous `ports.json` is no longer generated and not listed there, or when a retired port is handed to another model. Proved on a scratch copy (deleting `INSTRUMENT.LCR/4263A` → "LCR/4263A (port 15800) is no longer generated"; listing it clears it).
- **Every family reader uses `families.json`** — NODE.BareMetal `b510073` (`instruments/library.rs::family_directory`, Rust test `families_table_tests`; `Baremetal:Manager/node_paths.py`) and WEB.OsApi `0047b53` (`os_roots.family_directory()`/`family_name()`, `test_families_json_names_the_folder`) look the family up in `families.json` first, the prefix rule as fallback. Those images (orchestrator, OsApi) carry the change on rebuild.

Verified: `_komand/check.sh` (exit 0); `../AUDIO.komand/check.sh` still passes against this tree (99 tests, every derived file current).
- **Command tables corrected from vendor manuals** (owner-approved research, 2026-10-31; AUDIO.komand `check-tables --strict` 254 → 82). Every change is cited beside its table in `INSTRUMENT.<F>/<Model>/SOURCES.md` (manual title, URL, page/section); a finding no manual confirmed is listed there with what was searched and left as is. 43 duplicate entries are declared `"alias_of"` (new optional field, `_komand/schemas/command.schema.json`; the generator ignores it, so specs are unchanged). Fixed: DS1104Z, 66101A–66104A, 6060B, N9340B, 34401A, 33210A, 33220A, 54641D (short forms). Unconfirmed (manual not obtainable): 54641D enums, Porta_one, 4263A. Verified after each batch: `_komand/check.sh` and `../AUDIO.komand/check.sh` (both green; derived `.api.json`, `commands_tree.md`, `CommandList.csv/.xlsx` regenerated).
