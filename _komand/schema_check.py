#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""The INSTRUMENTS file formats, checked against their JSON Schemas.

The schemas are `_komand/schemas/*.schema.json` (draft 2020-12). This module
validates with the SUBSET of JSON Schema those files use — `type`, `required`,
`properties`, `patternProperties`, `additionalProperties`, `items`, `enum`,
`pattern`, `minimum`, `maximum`, `minLength`, `$ref` (local `#/$defs/x` and a
sibling `<name>.schema.json`) — so the check needs no pip install on any bench
and the root `check.sh instruments` lane runs it wherever Python 3 does. A
keyword outside that subset is refused, so a schema cannot silently stop
meaning what it says.

    python3 schema_check.py          # validate every file; exit 1 on any problem

`generate_device_apis.py --check` calls `check_tree()` too.
"""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(HERE, 'schemas')
ROOT = os.path.dirname(HERE)

KNOWN = {'$schema', '$id', 'title', 'description', '$defs', 'type', 'required', 'properties',
         'patternProperties', 'additionalProperties', 'items', 'enum', 'pattern', 'minimum',
         'maximum', 'minLength', '$ref'}

_TYPES = {
    'string': lambda v: isinstance(v, str),
    'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
    'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    'boolean': lambda v: isinstance(v, bool),
    'object': lambda v: isinstance(v, dict),
    'array': lambda v: isinstance(v, list),
    'null': lambda v: v is None,
}

_cache = {}


def load_schema(name):
    if name not in _cache:
        with open(os.path.join(SCHEMAS_DIR, name), 'r', encoding='utf-8') as f:
            _cache[name] = json.load(f)
    return _cache[name]


def validate(value, schema, root, where='$'):
    """Problems (strings) of `value` against `schema`; `root` resolves `#/$defs`."""
    problems = []
    unknown = set(schema) - KNOWN
    if unknown:
        return [f"{where}: schema uses unsupported keyword(s) {sorted(unknown)}"]
    if '$ref' in schema:
        ref = schema['$ref']
        if ref.startswith('#/$defs/'):
            return validate(value, root['$defs'][ref[len('#/$defs/'):]], root, where)
        target = load_schema(ref)
        return validate(value, target, target, where)
    if 'type' in schema:
        kinds = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(_TYPES[k](value) for k in kinds):
            return [f"{where}: expected {'/'.join(kinds)}, got {type(value).__name__}"]
    if 'enum' in schema and value not in schema['enum']:
        problems.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if 'minLength' in schema and len(value) < schema['minLength']:
            problems.append(f"{where}: shorter than {schema['minLength']}")
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            problems.append(f"{where}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'minimum' in schema and value < schema['minimum']:
            problems.append(f"{where}: {value} < {schema['minimum']}")
        if 'maximum' in schema and value > schema['maximum']:
            problems.append(f"{where}: {value} > {schema['maximum']}")
    if isinstance(value, list) and 'items' in schema:
        for i, item in enumerate(value):
            problems += validate(item, schema['items'], root, f"{where}[{i}]")
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                problems.append(f"{where}: missing required `{key}`")
        props = schema.get('properties', {})
        patterns = schema.get('patternProperties', {})
        extra = schema.get('additionalProperties', True)
        for key, item in value.items():
            path = f"{where}.{key}"
            if key in props:
                problems += validate(item, props[key], root, path)
                continue
            matched = [p for p in patterns if re.search(p, key)]
            for p in matched:
                problems += validate(item, patterns[p], root, path)
            if matched:
                continue
            if extra is False:
                problems.append(f"{where}: unknown key `{key}`")
            elif isinstance(extra, dict):
                problems += validate(item, extra, root, path)
    return problems


def check_file(path, schema_name):
    """Problems of one file, each prefixed with its path relative to INSTRUMENTS."""
    rel = os.path.relpath(path, ROOT)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        return [f"{rel}: unreadable — {e}"]
    schema = load_schema(schema_name)
    return [f"{rel}: {p}" for p in validate(doc, schema, schema)]


# Which files each schema governs, relative to INSTRUMENTS.
TARGETS = [
    ('manifest.json', 'manifest.schema.json'),
    ('families.json', 'families.schema.json'),
    ('INSTRUMENT.*/*/*.gui', 'gui.schema.json'),
    ('INSTRUMENT.*/*/*.komand', 'komand.schema.json'),
    ('INSTRUMENT.*/*/*.api.json', 'api.schema.json'),
    ('_komand/baselines/[!d]*.json', 'baseline.schema.json'),
]


def check_tree(root=ROOT):
    """(files checked, problems) over every governed file."""
    problems, n = [], 0
    for pattern, schema in TARGETS:
        for path in sorted(glob.glob(os.path.join(root, pattern))):
            n += 1
            problems += check_file(path, schema)
    return n, problems


def main():
    n, problems = check_tree()
    for p in problems:
        print(f"schema: {p}")
    print(f" {n} file(s) checked against _komand/schemas/; {len(problems)} problem(s).")
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
