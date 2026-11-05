#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""check_grab.py — every model's GRAB, stated (Doctrine: "Every instrument is grabbed").

Every instrument on the bench is grabbed, and a GRAB is compiled only from single
commands a unit on the bench answered (compile_grab.py → <Model>.qualified.json →
generate_device_apis.py → qualify_grab.py). So a model has one of three states, and this
says which, for every model of every family — nothing is left unstated:

    qualified   nab/GRAB compiled AND run on a unit (its `grab.qualified` evidence)
    compiled    nab/GRAB compiled from the bench's singles, not yet run on a unit
    none        no GRAB — with why: "never on the bench" (no <Model>.qualified.json),
                or "evidence not compiled" (the bench answered, nobody compiled it)

    python3 _komand/check_grab.py            # the table, then the totals
    python3 _komand/check_grab.py --check    # exit 1 when evidence was never compiled
    python3 _komand/check_grab.py --json     # one object per model

No model is named here; the folders are the list.
"""

import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def state_of(api_path):
    folder = os.path.dirname(api_path)
    model = os.path.basename(folder)
    family = os.path.basename(os.path.dirname(folder))
    try:
        with open(api_path, encoding='utf-8') as fh:
            nab = (json.load(fh).get('endpoints') or {}).get('nab') or {}
    except (OSError, ValueError) as err:
        return {'family': family, 'model': model, 'state': 'none', 'why': f'api.json unreadable: {err}'}
    grab = nab.get('GRAB')
    evidence = os.path.isfile(os.path.join(folder, f'{model}.qualified.json'))
    if grab:
        meta = grab.get('grab') or {}
        queries = len(meta.get('queries') or [])
        if meta.get('qualified'):
            units = (meta['qualified'] or {}).get('units') or []
            return {'family': family, 'model': model, 'state': 'qualified', 'queries': queries,
                    'why': f'{queries} queries, run on {len(units)} unit(s)'}
        return {'family': family, 'model': model, 'state': 'compiled', 'queries': queries,
                'why': f'{queries} queries, not yet run on a unit (qualify_grab.py)'}
    if evidence:
        return {'family': family, 'model': model, 'state': 'none', 'evidence': True,
                'why': 'evidence not compiled: the bench answered, run compile_grab.py + generate_device_apis.py'}
    return {'family': family, 'model': model, 'state': 'none', 'why': 'never on the bench: nothing to compile from'}


def states():
    return [state_of(p) for p in sorted(glob.glob(os.path.join(ROOT, 'INSTRUMENT.*', '*', '*.api.json')))
            if os.path.basename(p) == os.path.basename(os.path.dirname(p)) + '.api.json']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    rows = states()
    if args.json:
        print(json.dumps(rows, indent=1))
    elif not args.check:
        for r in rows:
            print(f"{r['family']:24} {r['model']:14} {r['state']:10} {r['why']}")
    totals = {}
    for r in rows:
        totals[r['state']] = totals.get(r['state'], 0) + 1
    stale = [r for r in rows if r.get('evidence')]
    if not args.json:
        print(f"GRAB: {len(rows)} models — " + ', '.join(f'{n} {k}' for k, n in sorted(totals.items())))
    if args.check and stale:
        for r in stale:
            print(f"❌ {r['family']}/{r['model']}: {r['why']}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
