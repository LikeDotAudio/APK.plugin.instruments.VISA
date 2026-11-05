# 🛣 Improvements — INSTRUMENTS (from the 2026-10-30 architecture audit)

What this repo should change to meet the standard, most valuable first. Source: [🔍Audits/ARCHITECTURE-AUDIT.md](../%F0%9F%94%8DAudits/ARCHITECTURE-AUDIT.md).
← [Roadmap](INDEX.md)

All audit items delivered — see 🌍Publishing/DELIVERY.md

## Open: the 54641D's screen dump is not the command its file says (2026-11-04)

`INSTRUMENT.Oscilloscope/54641D/54641D.api.json` declares `nab` / `get`
`Get_Display_Data` as `:DISPlay:DATA?` (marked `unverified`). WEB.OsApi's capture
recorder now asks every scope for its screen with that command (ROAD-3508,
`capture_recorder.Shooter`). Measured on the bench, at both 54641Ds (`gpib7,6`
and the second box): the bare query answers `-250,"Mass storage error"` /
`-420,"Query UNTERMINATED"` (VISA read error 15), and `BMP, SCReen, GRAYscale` and
`TIFF, SCReen, MONochrome` are refused with `-108,"Parameter not allowed"`. The
recorder backs off to every 15 minutes, so nothing is hammered.

**Do:** find the 54641D's real screen-image query in its programmer's guide (and
whether it needs a hardcopy destination set first), test it once from the
instrument page, and correct the file's `scpi`, dropping `unverified`. Until
then a bench can set the command in WEB.OsApi `config.ini [captures]
screen_devices`. **Done when:** `/api/os/captures/screens?device=visa/Oscilloscope/54641D/<box>`
lists pictures and the Recording display shows the scope's screen.
