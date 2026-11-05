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
        f'| **Inputs** | {cell(thing.get("inputs", "—"))} |',
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


def sdk_model(family, folder, m):
    api = m['api']
    name = m['name']
    lines = [f'# {name} — {family}', '', f'← [SDK]({link("../SDK.md")})', '']
    if not api:
        lines += ['No `api.json` is generated for this model yet: it has no `.komand` table to build one from.', '']
        return '\n'.join(lines)
    svc = api.get('service') or {}
    sock = svc.get('socket') or {}
    lines += [
        f'**{cell(api.get("manufacturer", ""))}** — {cell(api.get("notes", ""))}',
        '',
        '| | |',
        '|---|---|',
        f'| Channels | {api.get("channels", "")} |',
        f'| HTTP | `:{svc.get("port", "")}{svc.get("path", "")}` |',
    ]
    for k, v in (svc.get('routes') or {}).items():
        lines.append(f'| `{k}` | `{v}` |')
    for k, v in sock.items():
        lines.append(f'| socket `{k}` | `{v}` |')
    doms = api.get('domains') or {}
    if doms:
        lines.append('| Domains | ' + '; '.join(f'`{k}` {v.get("min", "")}…{v.get("max", "")} {v.get("units", "")}'
                                            for k, v in doms.items()) + ' |')
    tree = 'commands_tree.md' in m['files']
    sources = 'SOURCES.md' in m['files']
    if tree or sources:
        refs = []
        if tree:
            refs.append(f'[commands tree]({link(f"../../../{name}/commands_tree.md")})')
        if sources:
            refs.append(f'[sources]({link(f"../../../{name}/SOURCES.md")})')
        lines.append('| Reference | ' + ' · '.join(refs) + ' |')
    lines.append('')
    for verb in VERBS:
        eps = (api.get('endpoints') or {}).get(verb) or {}
        if not eps:
            continue
        lines += [f'## `{verb}` — {VERB_WHAT[verb]} ({len(eps)})', '',
                  '| Command | SCPI | Argument | Group | |', '|---|---|---|---|---|']
        for cmd, ep in eps.items():
            arg = ep.get('arg') or {}
            kind = arg.get('kind', '') if ep.get('args') else ''
            vals = arg.get('values')
            if isinstance(vals, list) and vals:
                kind = ' · '.join(str(v) for v in vals[:8]) + (' …' if len(vals) > 8 else '')
            flag = 'unverified' if ep.get('unverified') else ''
            lines.append(f'| `{cell(cmd)}` | `{cell(ep.get("scpi", ""))}` | {cell(kind)} | {cell(ep.get("group", ""))} | {flag} |')
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
        out[os.path.join(fdir, 'Documentation', MANUAL, 'SDK', f'{m["name"]}.md')] = sdk_model(family, folder, m)
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
