# Principles — INSTRUMENTS

The rules this library keeps, each with the code that keeps it. Ecosystem rules are cited, not copied: [Data handoff](../../../../../Documentation/%F0%9F%8F%9BPhilosophy/DATA%20HANDOFF%20PHILOSOPHY.md), [Dockers golden rule](../../../../../Documentation/%F0%9F%8F%9BPhilosophy/Dockers/goldenrule.md), [Refusal over fabrication](../../../../../Documentation/%F0%9F%8F%9BPhilosophy/Doctrine/readme.Refusal%20over%20fabrication.md).

← [Wiki home](../README.md)

| Principle | Kept by | Where it breaks |
|---|---|---|
| **Data, not a container.** No `Docker/`; images copy the folder in. | `NODE.BareMetal/Docker/Dockerfile` lines 74 and 253, `WEB.OsApi/Docker/Dockerfile` line 35, `DISCOVERY.Engine/Docker/Dockerfile` line 62, `DATABUS.Broker.MQTT/Docker/Dockerfile` line 62 | `SRC/` holds a crate, `apkaudio-plugin-instruments-visa`, whose `main.rs` only prints its name |
| **The prefix belongs to the directory.** `INSTRUMENT.DMM` is a folder; `DMM` is the type, topic, manifest key, tab and port lane. | `_komand/generate_device_apis.py` `family_name()` (line 36) / `family_directory()` (line 44); `AUDIO.komand/src/repository.rs` `family_name` | — |
| **One name per file.** `<Model>.api.json`, never `api.json`, so a path names its instrument. | `_komand/generate_device_apis.py` lines 1446–1454 sweep any bare `api.json` | — |
| **Derive, don't store — and show the cost.** `port = 15000 + family_index*100 + model_index`; `ports.json` is rewritten every run so a renumbering is a diff; a full lane or a duplicate port stops generation. | `generate_device_apis.py` `PORT_BASE` (line 77), `build_service_block()` (line 140), the `taken` check in `main()` (line 1430) | — |
| **Every class is declared.** A family folder with no `manifest.json` tab, or a tab with no folder, stops generation. | `generate_device_apis.py` `main()`; `--check` and the root `check.sh instruments` lane | — |
| **Reports are outputs.** `CommandList.csv/.xlsx`, every `commands_tree.md`, `knownDevices.json` links, `ports.json` and `<Model>.api.json` are generated and committed; each has a `--check` or is reproducible. | `AUDIO.komand` `build-list`, `build-trees`, `build-links` `--check`; `_komand/sort_komands.py --check` | Only the root `check.sh` default lanes run the Python ones; no CI runs any (see [Delivery](../%F0%9F%8C%8DPublishing/DELIVERY.md)) |
| **A command is declared or it is not sent.** KOMAND refuses anything a `.komand` table does not declare, so the tables are the whole vocabulary. | `AUDIO.komand/src/verbs/mod.rs` `refuse()` | — |
