#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""Sort every authored `.komand` table into display order, in place.

Each verb bucket (`set`, `do`, `rig`, `nab`) is reordered by
`generate_device_apis.command_order`: the `*` system commands first, then
alphabetical by SCPI. Nothing but the order changes — the files are written
back in the same shape they were read in. Run `generate_device_apis.py`
afterwards so the per-model `*.api.json` follow.

    python3 sort_komands.py          # rewrite the tables
    python3 sort_komands.py --check  # exit 1 if any table is out of order
"""
import glob
import json
import os
import sys

from generate_device_apis import INSTRUMENTS_ROOT, sorted_commands

VERBS = ('set', 'do', 'rig', 'nab')


def sort_table(document):
    for verb in VERBS:
        bucket = document.get(verb)
        if isinstance(bucket, dict):
            document[verb] = dict(sorted_commands(bucket))
    return document


def main():
    check = '--check' in sys.argv[1:]
    stale = []
    for path in sorted(glob.glob(os.path.join(INSTRUMENTS_ROOT, '*', '*', '*.komand'))):
        with open(path, encoding='utf-8') as f:
            text = f.read()
        body = json.dumps(sort_table(json.loads(text)), indent=2, ensure_ascii=False) + '\n'
        if body == text:
            continue
        stale.append(os.path.relpath(path, INSTRUMENTS_ROOT))
        if not check:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(body)
    verb = 'out of order' if check else 'sorted'
    for path in stale:
        print(f'{verb}: {path}')
    print(f'{len(stale)} table(s) {verb}.')
    return 1 if check and stale else 0


if __name__ == '__main__':
    sys.exit(main())
