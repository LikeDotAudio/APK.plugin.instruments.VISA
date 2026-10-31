# 🔍 Architecture audit — INSTRUMENTS (2026-10-30)

Audited against the APK.audio multi-repo architecture standard: coupling, boundaries, duplication, contracts.
← [Audits](INDEX.md) · Improvements: [🛣Roadmap/IMPROVEMENTS.md](../%F0%9F%9B%A3Roadmap/IMPROVEMENTS.md)

## Bounded context
The bench instrument library as data: 13 families / 181 models — family panel templates (`gui/`), per-model `<Model>.gui`, `<Model>.api.json`, 16 `<Model>.komand` SCPI tables, `manifest.json`, the `*IDN?` catalogue `_komand/knownDevices.json` (as crate `apkaudio-known-devices`), and the Python generator that derives every `api.json` and `ports.json`. 470 tracked files. Sampled: README, `manifest.json`, `_komand/{Cargo.toml,known_devices.rs,generate_device_apis.py,sort_komands.py}`, `INSTRUMENT.DMM/34401A/*`, `knownDevices.json` head, SMOKE.

## Context map
| Talks to | How (topic / endpoint / file / import) | Relationship |
|---|---|---|
| PLUGIN.VISA | Cargo git dep on `apkaudio-known-devices` (by rev), `include_str!("knownDevices.json")` | Customer–Supplier (versioned by git rev) |
| NODE.BareMetal orchestrator | `COPY ["PODS/POD.THICK/INSTRUMENTS", "./Instruments"]`; stamps family panels to `Gui/Panels/<device>` | Supplier of baked data (house rule: baked by design) |
| AUDIO.komand | reads `.komand` tables at `KOMAND_REPO_PATH=/app/Instruments`; owns `check-tables`, `build-list`, `build-trees` | Shared Kernel (file format with a schema, `_komand/schemas/komand.schema.json`) |
| WEB.OsApi | `os_roots.komand_library()`, serves `<Model>.api.json` (baked) | Conformist reader |
| `.apk.scripts/check.sh instruments` | runs the two Python `--check`s | Root-owned check |

## Scorecard
| Category | Score (0–3) | Finding |
|---|---|---|
| Coupling & Cohesion | 2 | Consumed by file copy into images (deliberate); the resolver is data (`families.json`) but three readers in other repos still re-implement it until they adopt it (handoffs). |
| Boundary Integrity | 3 | `<Model>.api.json` is a versioned published spec; every on-disk format has a JSON Schema. |
| Duplication Control | 3 | Catalogue fields checked equal across `.gui` and `knownDevices.json`; baselines and donors are data files. |
| Testing & Contracts | 3 | Schemas enforced by `--check`; a broken `.gui` fails loudly; one local `_komand/check.sh` (both checks, unit tests, cargo test). |
| Change management | 2 | `api_version` in every spec, legacy prefix still read; no deprecation path for a removed model's port. |
Score key: 3 meets the standard · 2 minor gaps · 1 significant gaps · 0 absent / violated.

## Findings
1. **Good: one copy, consumed by version.** [`_komand/Cargo.toml`](../../_komand/Cargo.toml) makes `knownDevices.json` a standalone crate so PLUGIN.VISA names it by git rev instead of walking up the tree.
2. **Good: derived, not stored.** Ports come from `15000 + family_index*100 + model_index` and `ports.json` is regenerated so renumbering shows as a diff; `--check` writes nothing and fails on drift.
3. **Good: a published spec with a version.** [`INSTRUMENT.DMM/34401A/34401A.api.json`](../../INSTRUMENT.DMM/34401A/34401A.api.json) carries `api_version`, an inbound `service` block and an outbound `transport` block; its shape is `_komand/schemas/api.schema.json`.
4. **Good: `knownDevices.json` is a model catalogue, not a discovery list.** It maps `*IDN?` model strings to metadata and holds no addresses.
5. **The resolver's other readers.** `families.json` is the resolver as data; the orchestrator (`instruments/library.rs`), `Baremetal:Manager/node_paths.py` and `WEB.OsApi/SRC/os_roots.py` still re-implement the prefix rule. **Waiting on NODE.BareMetal and WEB.OsApi (handoffs filed).**
6. **No deprecation path for a removed model's port.** A deleted model frees its port silently and the next model renumbers; open (a `retired` list in `ports.json` would make it a stated change).

Delivered findings are recorded in [🌍Publishing/DELIVERY.md](../%F0%9F%8C%8DPublishing/DELIVERY.md).
