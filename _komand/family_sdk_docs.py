#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""family_sdk_docs.py — every instrument family stands alone, with its SDK written out.

Each `INSTRUMENT.<Family>` is its own repository (a submodule of this one), so
each carries its own front door and its own SDK reference instead of leaning
on this repo's README. This writes, per family, from the family's own files:

    README.md                                       the front door
    Documentation/🧩Manual and Artifacts/SDK.md      every model, one line each
    Documentation/🧩Manual and Artifacts/SDK/<Model>.md
                                                    one model's whole command surface:
                                                    its routes, its sockets and every
                                                    verb's commands with their SCPI

The only authored input is the family's `thing.json` — what the thing IS on
the bench (an input, metering, monitoring, a source) and where its inputs are
read from. Everything else is read off `<Model>/<Model>.api.json`, which
generate_device_apis.py writes from the `.komand` tables. No model is named here.

    python3 _komand/family_sdk_docs.py            # write
    python3 _komand/family_sdk_docs.py --check    # exit 1 when a page is stale
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANUAL = '🧩Manual and Artifacts'
SMOKE_BLOCK = re.compile(r'<!-- wiki:smoke -->.*?<!-- /wiki:smoke -->', re.S)
VERBS = ('get', 'set', 'nab', 'rig', 'do')
VERB_WHAT = {
    'get': 'reads one value',
    'set': 'writes one value',
    'nab': 'reads more than one thing (observation, telemetry)',
    'rig': 'configures several arguments at once',
    'do': 'executes an action; takes no value',
}
ROLE_WHAT = {
    'inputs': 'takes signals in — its connectors are inputs a patch can land on',
    'metering': 'measures — its readings are numbers with units',
    'monitoring': 'shows — a trace, a waveform or a display you watch',
    'source': 'puts something out — a stimulus, a supply or a load',
}


def families():
    with open(os.path.join(ROOT, 'families.json'), encoding='utf-8') as f:
        return json.load(f)['families']


def link(path):
    return quote(path)


def cell(text):
    return str(text if text is not None else '').replace('|', '\\|').replace('\n', ' ').strip()


def load_models(fdir):
    out = []
    for name in sorted(os.listdir(fdir)):
        mdir = os.path.join(fdir, name)
        if name.startswith(('.', '_')) or name in ('gui', 'Documentation') or not os.path.isdir(mdir):
            continue
        api_path = os.path.join(mdir, f'{name}.api.json')
        api = None
        if os.path.isfile(api_path):
            with open(api_path, encoding='utf-8') as f:
                api = json.load(f)
        files = sorted(os.listdir(mdir))
        out.append({'name': name, 'api': api, 'files': files})
    return out


def front_door(family, folder, thing, models, gui):
    roles = thing.get('roles') or []
    lines = [
        f'# {folder}',
        '',
        f'**Wiki:** [Documentation/README.md](Documentation/README.md) — principles, architecture, delivery, '
        f'and the [SDK]({link(f"Documentation/{MANUAL}/SDK.md")}).',
        '',
        f'The **{family}** instruments of the APK.audio bench, as one thing: {len(models)} models, '
        f'their command tables and the family\'s panel. {cell(thing.get("about", ""))}',
        '',
        '| | |',
        '|---|---|',
        '| **Is** | ' + ('<br>'.join(f'**{r}** — {ROLE_WHAT.get(r, "")}' for r in roles) or '—') + ' |',
        f'| **Inputs and outputs** | {cell(thing.get("io") or thing.get("inputs") or "—")} |',
        f'| **Recipe** | none — data, not a container: read in place by the stacks that bake `INSTRUMENTS` |',
        f'| **Source** | this repository ({cell(thing.get("repository", ""))}), a submodule of '
        f'[APK.plugin.instruments.VISA](https://github.com/LikeDotAudio/APK.plugin.instruments.VISA) at `{folder}/` |',
        f'| **Family name** | `{family}` — the device type, the topic segment and the `manifest.json` key; '
        f'the `INSTRUMENT.` prefix belongs to the folder only |',
        '',
        '## Models',
        '',
        '| Model | Maker | What | Commands | Table | API |',
        '|---|---|---|---:|:---:|---|',
    ]
    for m in models:
        api = m['api'] or {}
        total = (api.get('summary') or {}).get('total_commands', '')
        table = '✅' if f'{m["name"]}.komand' in m['files'] else ''
        sdk = link(f'Documentation/{MANUAL}/SDK/{m["name"]}.md')
        port = ((api.get('service') or {}).get('port')) or ''
        lines.append(f'| [{cell(m["name"])}]({sdk}) | {cell(api.get("manufacturer", ""))} | {cell(api.get("notes", ""))} '
                     f'| {total} | {table} | {f":{port}" if port else ""} |')
    lines += [
        '',
        '## Layout',
        '',
        '```',
        f'{folder}/',
        '  thing.json            what this thing is on the bench (authored)',
        '  gui/                  the family panel, stamped once per discovered box',
    ]
    for g in gui:
        lines.append(f'    {g}')
    lines += [
        '  <Model>/              <Model>.komand (the command table), <Model>.gui,',
        '                        <Model>.api.json (generated), commands_tree.md, SOURCES.md',
        '  Documentation/        the wiki; SDK/ is generated by _komand/family_sdk_docs.py',
        '```',
        '',
        'Generated by `_komand/family_sdk_docs.py` in the parent repository; edit `thing.json` or the',
        'models, not this page.',
        '',
    ]
    return '\n'.join(lines)


def sdk_index(family, folder, models):
    lines = [
        f'# SDK — {folder}',
        '',
        f'Every {family} model this library drives, and how to drive it. Each model answers the same five '
        'verbs over HTTP (its own port), WebSocket, a Unix socket and the bus; one page per model below '
        'lists its routes and every command.',
        '',
        '← [Manual and Artifacts](INDEX.md)',
        '',
        '| Verb | What it does |',
        '|---|---|',
    ]
    lines += [f'| `{v}` | {VERB_WHAT[v]} |' for v in VERBS]
    lines += ['', '| Model | Maker | get | set | nab | rig | do | Port |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for m in models:
        api = m['api'] or {}
        s = api.get('summary') or {}
        port = (api.get('service') or {}).get('port', '')
        lines.append(f'| [{cell(m["name"])}]({link("SDK/" + m["name"] + ".md")}) | {cell(api.get("manufacturer", ""))} | '
                     + ' | '.join(str(s.get(f'{v}_count', '')) for v in VERBS) + f' | {port} |')
    lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------- inputs and outputs

# The box's connectors live in ONE place, the BIM library (DATABASE.server.BIM,
# one part per device type). This reads that checkout when it is beside this one
# and writes the I/O section from it; a checkout without it (this repo cloned
# alone) keeps the section already on the page, so --check agrees in both.
BIM_LIBRARY = os.path.normpath(os.path.join(ROOT, '..', '..', 'POD.database', 'DATABASE.server.BIM', 'SRC', 'library'))
IO_BLOCK = re.compile(r'<!-- sdk:io -->.*?<!-- /sdk:io -->', re.S)
MAINS = re.compile(r'mains|\bac\b|line in|iec|power in|power inlet', re.I)
SIDES = (('input', 'Inputs'), ('output', 'Outputs'), ('connection', 'Connections (control and network)'))


def norm(model):
    return re.sub(r'[^A-Z0-9]', '', str(model or '').upper())


_BIM = None


def bim_index():
    """norm(model) -> [part] for every BIM part, read once; {} when the library is not here."""
    global _BIM
    if _BIM is None:
        _BIM = {}
        if os.path.isdir(BIM_LIBRARY):
            for maker in sorted(os.listdir(BIM_LIBRARY)):
                mdir = os.path.join(BIM_LIBRARY, maker)
                if not os.path.isdir(mdir):
                    continue
                for name in sorted(os.listdir(mdir)):
                    if not name.endswith('.bim.json'):
                        continue
                    try:
                        with open(os.path.join(mdir, name), encoding='utf-8') as fh:
                            part = json.load(fh)
                    except (OSError, ValueError):
                        continue
                    # The model itself first, then its aliases: an exact model always
                    # outranks another part's alias for it.
                    for rank, key in enumerate([part.get('model')] + list(part.get('model_aka') or [])):
                        if key:
                            _BIM.setdefault(norm(key), []).append((min(rank, 1), part))
    return _BIM


def bim_part(family, model):
    """The BIM part for a model folder: its name, or the name without a maker prefix
    (`HP_8903B` -> 8903B); a part of this family first, then any Test & Measurement part."""
    idx = bim_index()
    keys = [norm(model)]
    if '_' in model:
        keys.append(norm(model.split('_', 1)[1]))
    for key in keys:
        parts = [p for _rank, p in sorted(idx.get(key) or [], key=lambda rp: rp[0])]
        for want in (lambda p: str(p.get('class', '')).lower() == family.lower(),
                     lambda p: p.get('category') == 'Test & Measurement',
                     lambda p: True):
            hit = [p for p in parts if want(p)]
            if hit:
                return hit[0]
    return None


def io_section(family, m, thing=None):
    lines = ['<!-- sdk:io -->', '## Inputs and outputs — the box', '']
    # A model the family's thing.json says has no box (a reference model, an
    # emulator) has no connectors to state, and so no BIM part to look for.
    no_box = ((thing or {}).get('no_box') or {}).get(m['name'])
    if no_box:
        lines += [f'This model has no physical box, so it has no connectors: {cell(no_box)} '
                  'Its inputs and outputs are its commands and bus topics, below.', '', '<!-- /sdk:io -->']
        return '\n'.join(lines)
    part = bim_part(family, m['name'])
    if not part:
        lines += ['No part for this model in the BIM library yet (`DATABASE.server.BIM`), so its connectors are not '
                  'stated here. Add the part there — the one place a device type is described — and regenerate.',
                  '', '<!-- /sdk:io -->']
        return '\n'.join(lines)
    ports = part.get('ports') or []
    lines += [f'From the BIM part [`{part.get("id", "")}`](/api/bim/parts?full=1&id={quote(str(part.get("id", "")))}) '
              f'— {cell(part.get("note") or part.get("stage") or "")}', '']
    # Mains is the box's own supply, said once at the foot; a DC load's or a
    # supply's power terminals are its real inputs and outputs and stay in the tables.
    def is_mains(p):
        text = ' '.join(str(p.get(k, '')) for k in ('terminal', 'group', 'connector', 'signal'))
        return p.get('domain') == 'power' and p.get('side') in ('input', 'supply') and bool(MAINS.search(text))
    for side, title in SIDES:
        rows = [p for p in ports if p.get('side') == side and not is_mains(p)]
        if not rows:
            continue
        lines += [f'### {title}', '', '| Terminal | Connector | Domain | Count | Signal |', '|---|---|---|---:|---|']
        for p in rows:
            lines.append(f'| {cell(p.get("terminal") or p.get("group"))} | {cell(p.get("connector"))} | {cell(p.get("domain"))} '
                         f'| {p.get("count", 1)} | {cell(p.get("signal"))} |')
        lines.append('')
    power = [p for p in ports if is_mains(p)]
    if power:
        lines.append('**Power:** ' + '; '.join(cell(p.get("terminal") or p.get("group")) + (f' ({cell(p["connector"])})' if p.get('connector') else '')
                                           for p in power))
        lines.append('')
    lines.append('<!-- /sdk:io -->')
    return '\n'.join(lines)


def arg_text(ep):
    """What a command takes: its arguments, their kind, range, choices and unit."""
    args = ep.get('args') or []
    if not args:
        return '—'
    arg = ep.get('arg') or {}
    bits = []
    vals = arg.get('values')
    if isinstance(vals, list) and vals:
        bits.append(' · '.join(f'`{v}`' for v in vals[:10]) + (' …' if len(vals) > 10 else ''))
    elif arg.get('kind') and arg.get('kind') != 'none':
        bits.append(str(arg['kind']))
    rng = [str(arg[k]) for k in ('min', 'max') if k in arg]
    if rng:
        bits.append('…'.join(rng) if len(rng) == 2 else ('≥ ' if 'min' in arg else '≤ ') + rng[0])
    if arg.get('limits'):
        bits.append(f'limits: {arg["limits"]}')
    if arg.get('unit'):
        bits.append(str(arg['unit']))
    names = ', '.join(f'`{a}`' for a in args)
    return f'{names}: ' + ' '.join(bits) if bits else names


def out_text(ep):
    """What a command gives back, and where."""
    ret = ep.get('returns')
    if not ret:
        return '—'
    kind = ret.get('type', '') if isinstance(ret, dict) else str(ret)
    count = ret.get('count') if isinstance(ret, dict) else None
    reading = (ep.get('mqtt') or {}).get('reading_topic', '')
    leaf = reading.split('/Reading/', 1)[1] if '/Reading/' in reading else ''
    return f'{kind}{f" ×{count}" if count and count != 1 else ""}' + (f' → `…/Reading/{leaf}`' if leaf else '')


def drive_section(family, name, api):
    eps = api.get('endpoints') or {}
    sample = None
    for verb in ('set', 'do', 'nab', 'get', 'rig'):
        if eps.get(verb):
            sample = next(iter(eps[verb].values()))
            break
    path = (api.get('service') or {}).get('path', f'/api/instrument/{family}/{name}')
    lines = ['## Driving it', '',
             'Three doors, all on the bench\'s own services — none of them is a per-model process.', '',
             '1. **The bus, through KOMAND** (what a panel and the touch pad do). Teach the topic its handler, then send the '
             'value; never retained — KOMAND ignores a retained value on purpose. `target` is the box\'s Write topic '
             '(`GET /api/instrument/status?protocol=visa&resource=…` → `write_topic`); a DO/NAB fires on a truthy value.', '']
    if sample:
        handler = {'enable': True, 'komand_type': sample.get('verb', 'set'), 'command': sample.get('command'),
                   'model': name, 'input_name': (sample.get('args') or [''])[0], 'target': '<box>/Write'}
        value = 'true' if sample.get('verb') in ('do', 'nab', 'get') else '<value>'
        lines += ['```sh',
                  f"T=APK.audio/Gui/MyPanel/{sample.get('command')}",
                  f"mosquitto_pub -t \"$T/config\" -m '{json.dumps({'komand_handler': handler})}'",
                  f"mosquitto_pub -t \"$T\" -m '{{\"value\": {value}}}'",
                  '```', '']
    lines += ['2. **Raw SCPI** — `POST /api/instrument/send` with `{"protocol": "visa", "resource": "<VISA resource>", '
              '"command": "<SCPI>"}`; the answer comes back in the reply and on `<box>/Read`.', '',
              f'3. **The spec, over HTTP** — `GET {path}` (this model\'s whole `api.json`), `GET {path}/<verb>/<command>` '
              '(one command\'s entry), `GET …/health`. These describe; they do not send anything to the box.', '',
              'A read\'s answer is published on `<box>/Reading/<command>` (the **Out** column below); `<box>` is '
              '`APK.audio/System/Protocols/visa/Device/<Family>/<Model>/<Dev…>`.', '']
    return lines


def sdk_model(family, folder, m, old='', thing=None):
    api = m['api']
    name = m['name']
    lines = [f'# {name} — {family}', '', f'← [SDK]({link("../SDK.md")})', '']
    if not api:
        lines += ['No `api.json` is generated for this model yet: it has no `.komand` table to build one from.', '']
        return '\n'.join(lines)
    svc = api.get('service') or {}
    lines += [f'**{cell(api.get("manufacturer", ""))}** — {cell(api.get("notes", ""))}', '',
              '| | |', '|---|---|',
              f'| Family | `{family}` |',
              f'| Channels | {api.get("channels", "")} |',
              f'| Spec | `GET {svc.get("path", "")}` |',
              f'| Default transport | `{(api.get("transport") or {}).get("default", "")}` |']
    doms = api.get('domains') or {}
    if doms:
        lines.append('| Ranges | ' + '; '.join(f'`{k}` {v.get("min", "")}…{v.get("max", "")} {v.get("units", "")}'
                                           for k, v in doms.items()) + ' |')
    refs = []
    if 'commands_tree.md' in m['files']:
        refs.append(f'[commands tree]({link(f"../../../{name}/commands_tree.md")})')
    if 'SOURCES.md' in m['files']:
        refs.append(f'[sources]({link(f"../../../{name}/SOURCES.md")})')
    if refs:
        lines.append('| Reference | ' + ' · '.join(refs) + ' |')
    lines.append('')
    # Inputs and outputs of the box: from BIM when its checkout is here, else the page's own.
    io = io_section(family, m, thing) if bim_index() else None
    if io is None:
        kept = IO_BLOCK.search(old or '')
        io = kept.group(0) if kept else '<!-- sdk:io -->\n## Inputs and outputs — the box\n\nThe BIM library was not beside this checkout when this page was written.\n\n<!-- /sdk:io -->'
    lines += [io, '']
    lines += drive_section(family, name, api)
    total = sum(len((api.get('endpoints') or {}).get(v) or {}) for v in VERBS)
    lines += [f'## Commands ({total}) — inputs and outputs of the API', '',
              '**In** is what the command takes; **Out** is what it gives back and where. Every command arrives on '
              f'`APK.audio/Gui/Komands/{family}/<Command>`.', '']
    for verb in VERBS:
        eps = (api.get('endpoints') or {}).get(verb) or {}
        if not eps:
            continue
        lines += [f'### `{verb}` — {VERB_WHAT[verb]} ({len(eps)})', '',
                  '| Command | SCPI | In | Out | Group | |', '|---|---|---|---|---|---|']
        for cmd, ep in eps.items():
            flag = 'unverified' if ep.get('unverified') else ''
            lines.append(f'| `{cell(cmd)}` | `{cell(ep.get("scpi", ""))}` | {cell(arg_text(ep))} | {cell(out_text(ep))} '
                         f'| {cell(ep.get("group", ""))} | {flag} |')
        lines.append('')
    return '\n'.join(lines)


def pages(family, folder):
    fdir = os.path.join(ROOT, folder)
    thing_path = os.path.join(fdir, 'thing.json')
    thing = {}
    if os.path.isfile(thing_path):
        with open(thing_path, encoding='utf-8') as f:
            thing = json.load(f)
    models = load_models(fdir)
    gdir = os.path.join(fdir, 'gui')
    gui = sorted(os.listdir(gdir)) if os.path.isdir(gdir) else []
    readme = os.path.join(fdir, 'README.md')
    door = front_door(family, folder, thing, models, gui)
    # The smoke verdict (.apk.scripts/smoke.py) is written INTO this page by its
    # own tool; it is carried over unchanged, never regenerated here.
    if os.path.isfile(readme):
        with open(readme, encoding='utf-8') as f:
            kept = SMOKE_BLOCK.search(f.read())
        if kept:
            door = f'{door}\n{kept.group(0)}\n'
    out = {readme: door,
           os.path.join(fdir, 'Documentation', MANUAL, 'SDK.md'): sdk_index(family, folder, models)}
    for m in models:
        page = os.path.join(fdir, 'Documentation', MANUAL, 'SDK', f'{m["name"]}.md')
        prior = ''
        if os.path.isfile(page):
            with open(page, encoding='utf-8') as fh:
                prior = fh.read()
        out[page] = sdk_model(family, folder, m, prior, thing)
    return out, os.path.join(fdir, 'Documentation', MANUAL, 'SDK')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='change nothing; exit 1 if a page is stale')
    ap.add_argument('families', nargs='*', help='only these family names')
    a = ap.parse_args()
    stale = []
    written = 0
    for family, folder in families().items():
        if a.families and family not in a.families:
            continue
        want, sdk_dir = pages(family, folder)
        have = set()
        if os.path.isdir(sdk_dir):
            have = {os.path.join(sdk_dir, n) for n in os.listdir(sdk_dir) if n.endswith('.md')}
        for extra in sorted(have - set(want)):
            stale.append(f'{os.path.relpath(extra, ROOT)} (no such model)')
            if not a.check:
                os.remove(extra)
        for path, text in want.items():
            old = None
            if os.path.isfile(path):
                with open(path, encoding='utf-8') as f:
                    old = f.read()
            if old == text:
                continue
            stale.append(os.path.relpath(path, ROOT))
            if not a.check:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                written += 1
    if a.check:
        for s in stale:
            print(f'stale: {s}')
        print(f'{"FAIL" if stale else "ok"}   family SDK pages: {len(stale)} stale')
        return 1 if stale else 0
    print(f'wrote {written} family SDK page(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
