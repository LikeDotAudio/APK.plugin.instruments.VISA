# 🛣 Improvements — INSTRUMENTS (from the 2026-10-30 architecture audit)

What this repo should change to meet the standard, most valuable first. Source: [🔍Audits/ARCHITECTURE-AUDIT.md](../%F0%9F%94%8DAudits/ARCHITECTURE-AUDIT.md).
← [Roadmap](INDEX.md)

All audit items delivered — see 🌍Publishing/DELIVERY.md

## Delivered 2026-11-04: the 54641D's screen dump, measured

The 54641D's screen is `:DISPlay:DATA? TIFF, SCReen`, measured on the bench. It
returns a 24 KB baseline TIFF, 512×349 8-bit grey with PackBits compression.
`TIFF, GRATicule` returns only the grid. The bare query its file declares answers
`-250 "Mass storage error"`, and the BMP and palette arguments are refused with
`-108`.

The fix is NOT in `54641D.komand`. The 54641D is the Oscilloscope family's donor
(`_komand/baselines/donors.json`), so regenerating writes its table into all 32
unauthored scopes' `.api.json`, the Rigols included, whose bare query is right,
and marks it verified there. WEB.OsApi's capture recorder therefore carries
measured per-model commands (`config.ini [captures] screen_models`). Recording
shows the scope's screen, served as PNG.

The underlying limit is that a donor table cannot carry one model's measured
answer without carrying it to every unauthored model. Authoring a `.komand` for a
model is what separates it from the donor.
