#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""compile_grab.py — what each model answered ALONE on the bench, kept beside its tables.

    python3 compile_grab.py                       # from the bench's OsApi (localhost:8080)
    python3 compile_grab.py --from evidence.json  # from a saved /qualified answer
    python3 compile_grab.py --url http://host:8080/api/os/captures/qualified
    then: python3 generate_device_apis.py        # every model with evidence gets its GRAB

GRAB IS COMPILED FROM SUCCESSFUL SINGLE COMMANDS (owner, 2026-11-04). A library
file is a family's, and a model may not know every query in it; a stacked query
with one unknown header in it spoils the whole answer. So nothing goes into a
GRAB on the strength of the table: WEB.OsApi's Nabber asks each query ALONE, once
per unit, and records the outcome (`nab_known`); `/api/os/captures/qualified`
reports, per model, the queries ANY unit answered alone (the union), and the
ones a unit refused. This script maps each qualified query back to the model's
own library endpoint (by its `scpi_fast` or `scpi`) and writes
`<family>/<Model>/<Model>.qualified.json` — the bench's evidence, committed with
the tables. `generate_device_apis.py` compiles the GRAB from that file and from
nothing else.

WHAT QUALIFIES: a query the bench answered alone that IS one of the model's
`get`/`nab` endpoints, takes no argument, asks one thing (no `;`), and does not
return a block (a screen dump is not a setting). A refused query is listed with
its reason; one never qualified on any unit is left out.

A model with no evidence keeps no file and gets no GRAB. Re-running replaces a
model's file with the bench's current answer, so a unit that has learned more
widens its GRAB, and a query a unit has since refused leaves it.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_device_apis as gen  # noqa: E402

DEFAULT_URL = 'http://localhost:8080/api/os/captures/qualified'


def norm(query):
    """A query as the instrument hears it: upper-case, no spaces, one leading `:` at most."""
    return ''.join(str(query).split()).upper()


def endpoint_index(api):
    """{normalised query: (endpoint name, query as the library spells it)} for the model's single, arg-free queries."""
    index = {}
    endpoints = api.get('endpoints', {})
    for verb in ('get', 'nab'):
        for name, ep in (endpoints.get(verb) or {}).items():
            if name.startswith('GRAB'):
                continue
            returns = ep.get('returns') or {}
            if ep.get('args') or (isinstance(returns, dict) and str(returns.get('type', '')).upper() == 'BLOCK'):
                continue
            for spelled in (ep.get('scpi_fast'), ep.get('scpi')):
                if not spelled or '?' not in spelled or ';' in spelled or '<' in spelled:
                    continue
                index.setdefault(norm(spelled), (name, spelled.strip()))
                index.setdefault(norm(spelled).lstrip(':'), (name, spelled.strip()))
    return index


def compile_model(model, evidence, api, now=None):
    """The `.qualified.json` document for one model, or None when nothing qualifies."""
    index = endpoint_index(api)
    commands, seen = [], set()
    for q in evidence.get('qualified', []):
        hit = index.get(norm(q['command'])) or index.get(norm(q['command']).lstrip(':'))
        if hit is None or hit[0] in seen:
            continue
        seen.add(hit[0])
        commands.append({'endpoint': hit[0], 'query': q['command'], 'units': q.get('units', []),
                         'first': q.get('first')})
    if not commands:
        return None
    # The library's own order, so a GRAB's answers come back in a stable, readable order.
    order = {name: i for i, name in enumerate(list((api.get('endpoints', {}).get('get') or {}))
                                             + list((api.get('endpoints', {}).get('nab') or {})))}
    commands.sort(key=lambda c: (order.get(c['endpoint'], 1 << 30), c['endpoint']))
    refused = [{'query': r['command'], 'why': r.get('why')} for r in evidence.get('refused', [])]
    return {
        'model': model,
        'family': api.get('family') or evidence.get('family'),
        'compiled': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
        'source': 'WEB.OsApi /api/os/captures/qualified (Nabber nab_known: each query asked alone, once per unit)',
        'units': evidence.get('units', []),
        'commands': commands,
        'refused': refused,
    }


def main(argv):
    url = DEFAULT_URL
    source = None
    if '--from' in argv:
        source = argv[argv.index('--from') + 1]
    if '--url' in argv:
        url = argv[argv.index('--url') + 1]
    if source:
        with open(source, encoding='utf-8') as fh:
            models = json.load(fh).get('models', {})
    else:
        with urllib.request.urlopen(url, timeout=20) as res:
            models = json.load(res).get('models', {})
    wrote = 0
    for model, evidence in sorted(models.items()):
        family = evidence.get('family')
        try:
            folder = gen.family_directory(family)
        except (KeyError, ValueError, TypeError):
            print(f'  skip {family}/{model}: no such family in families.json')
            continue
        api_path = os.path.join(folder, model, f'{model}.api.json')
        if not os.path.isfile(api_path):
            print(f'  skip {family}/{model}: no {model}.api.json in the library')
            continue
        with open(api_path, encoding='utf-8') as fh:
            api = json.load(fh)
        doc = compile_model(model, evidence, api)
        if doc is None:
            print(f'  {family}/{model}: nothing qualified yet')
            continue
        out = os.path.join(folder, model, f'{model}.qualified.json')
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(doc, indent=2) + '\n')
        wrote += 1
        print(f'  {family}/{model}: {len(doc["commands"])} qualified, {len(doc["refused"])} refused '
              f'-> {os.path.relpath(out, gen.INSTRUMENTS_ROOT)}')
    print(f'{wrote} model(s) written; run generate_device_apis.py to compile their GRAB.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
