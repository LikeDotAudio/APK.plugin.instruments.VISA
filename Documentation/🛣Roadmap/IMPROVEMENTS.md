# 🛣 Improvements — INSTRUMENTS (from the 2026-10-30 architecture audit)

What this repo should change to meet the standard, most valuable first. Source: [🔍Audits/ARCHITECTURE-AUDIT.md](../%F0%9F%94%8DAudits/ARCHITECTURE-AUDIT.md).
← [Roadmap](INDEX.md)

| # | Improvement | Category | Effort (S/M/L) | Evidence |
|---|---|---|---|---|
| 1 | Have the orchestrator, `Baremetal:Manager/node_paths.py` and `WEB.OsApi/SRC/os_roots.py` resolve families from `families.json`. **Waiting on NODE.BareMetal / WEB.OsApi (handoffs filed).** | Duplication Control | S | `families.json` |
| 2 | Give a removed model's port a stated retirement (e.g. `retired` in `ports.json`) so renumbering is never silent. | Change management | S | `_komand/ports.json` |

Delivered items: see [🌍Publishing/DELIVERY.md](../%F0%9F%8C%8DPublishing/DELIVERY.md).
