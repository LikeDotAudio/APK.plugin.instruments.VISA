#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""A SET with options is a SELECTOR *and* one SET per option (owner, 2026-11-11).

    python3 _komand/expand_selectors.py           # write every <Model>.komand
    python3 _komand/expand_selectors.py --check   # write nothing; exit 1 if a table is stale

"Selects the primary measurement parameter (e.g. CP, CS, LP, LS, R, Z) … each should be a
SET command … since we have a few fixed ones, having each iterated helps simplify things
… the same for all devices … if there are options, make it a selector AND individuals."

So for every `set` entry whose arg lists its options (`arg.values`) and whose SCPI carries
exactly one `<placeholder>`, the table keeps the selector (`Primary_Parameter <param>`) and
holds one argument-less SET per option, named `<Selector>_<OPTION>`:

    Primary_Parameter        :CALCulate1:FORMat <param>     arg.values [CP, CS, …]
    Primary_Parameter_CP     :CALCulate1:FORMat CP
    Primary_Parameter_CS     :CALCulate1:FORMat CS          …

`<Selector>_ON` / `_OFF` is the name KOMAND's set.rs already falls back to for a boolean
press, so a bool selector's individuals are exactly the pair it looks for.

An individual is GENERATED: its `notes` start with MARK and name its selector; a re-run
rewrites it from the selector, drops it when the option or selector is gone, and changes
nothing when nothing changed. A hand-written command already holding the name wins and is
reported, never overwritten. `arg.labels` ({option: words}) feeds the individual's
description when the selector has it. Every individual is `unverified` until the bench
sends it — the selector being proven proves the path, not each option.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MARK = "Individual of selector "
VERBS = ("set", "do", "rig", "nab")
sys.path.insert(0, HERE)
from sort_komands import sort_table  # noqa: E402  — one display order, the sorter's

PH = re.compile(r"<([A-Za-z_][A-Za-z0-9_]*)>")


def token(option: str) -> str:
    """The option as a name part: quotes dropped, anything else not [A-Za-z0-9] → '_'."""
    t = re.sub(r"[^A-Za-z0-9]+", "_", str(option).replace('"', "").replace("'", ""))
    return t.strip("_")


def generated(cmd: dict) -> bool:
    return str(cmd.get("notes", "")).startswith(MARK)


def individuals(name: str, sel: dict) -> dict:
    """The individual SETs one selector stands for ({} when it lists no options)."""
    arg = sel.get("arg") or {}
    values = arg.get("values") or []
    if not values or generated(sel):
        return {}
    phs = PH.findall(sel.get("scpi", ""))
    if len(set(phs)) != 1:
        return {}
    ph = f"<{phs[0]}>"
    labels = arg.get("labels") or {}
    out = {}
    for v in values:
        t = token(v)
        if not t:
            continue
        iname = f"{name}_{t}"
        if iname in out:
            continue
        label = labels.get(v)
        desc = f"{name} → {v}" + (f" ({label})" if label else "") + f". {sel.get('description', '')}".rstrip()
        cmd = {"scpi": sel["scpi"].replace(ph, str(v))}
        fast = sel.get("scpiFast") or sel.get("scpi_fast")
        if fast and ph in fast:
            cmd["scpiFast"] = fast.replace(ph, str(v))
        cmd["description"] = desc
        for k in ("subsystem", "group"):
            if k in sel:
                cmd[k] = sel[k]
        cmd["unverified"] = True
        cmd["notes"] = (f"{MARK}{name} = {v} — written by _komand/expand_selectors.py from the "
                        f"selector; edit the selector (its arg.values / arg.labels), not this. "
                        f"Unverified until the bench sends this option.")
        out[iname] = cmd
    return out


def expand(table: dict):
    """(new table, notes about names a hand-written command already holds)."""
    sets = table.get("set") or {}
    taken = {n for v in VERBS for n, c in (table.get(v) or {}).items() if not generated(c)}
    want = {}
    clashes = []
    for name, sel in sets.items():
        for iname, cmd in individuals(name, sel).items():
            if iname in taken:
                clashes.append(iname)
                continue
            want[iname] = cmd
    new_set = {}
    for name, cmd in sets.items():
        if generated(cmd):
            continue  # every generated entry is rebuilt (or dropped) below
        new_set[name] = cmd
        for iname, icmd in individuals(name, cmd).items():
            if iname in want:
                new_set[iname] = want[iname]
    out = dict(table)
    out["set"] = new_set
    return out, clashes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    stale, total = [], 0
    for path in sorted(glob.glob(os.path.join(ROOT, "INSTRUMENT.*", "*", "*.komand"))):
        raw = open(path, encoding="utf-8").read()
        table = json.loads(raw)
        new, clashes = expand(table)
        total += sum(1 for c in new["set"].values() if generated(c))
        for c in clashes:
            print(f"   ⚠ {os.path.relpath(path, ROOT)}: {c} is hand-written — kept, not generated")
        if new == table:          # dict equality: order is the sorter's business, not ours
            continue
        text = json.dumps(sort_table(new), indent=2, ensure_ascii=False) + ("\n" if raw.endswith("\n") else "")
        stale.append(os.path.relpath(path, ROOT))
        if not a.check:
            open(path, "w", encoding="utf-8").write(text)
    if a.check:
        if stale:
            print(f"   ❌ {len(stale)} table(s) without their selector individuals:")
            for s in stale:
                print(f"      {s}")
            return 1
        print(f"   ✅ every selector has its individuals ({total})")
        return 0
    print(f"   ✅ {len(stale)} table(s) written; {total} individual SET(s) in all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
