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

- No CI in this repo and no pre-build gate runs any check above. The root `check.sh` runs the two Python checks in its default lanes, but only when someone runs it; the `AUDIO.komand` cargo checks are run by hand.
- Images are rebuilt by hand; nothing rebuilds them on a push here.
- No live URL of its own; the library surfaces through the OsApi instrument page on the bench.
