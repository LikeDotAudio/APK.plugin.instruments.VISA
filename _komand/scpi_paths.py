#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""scpi_paths.py — every SCPI header in every `.komand` is a path in its model's own tree.

THE FAULT THIS GUARDS (owner, 2026-11-11, the 33220A page): the table generator
once cut the parent off a manual's command, leaving an ORPHAN whose path is only
the tail of a real one — `:BEEPer:STATe?` for `SYSTem:BEEPer:STATe?`,
`:ATTRibute:POINts?` for `DATA:ATTRibute:POINts?`, `:SPI:CLK` for
`:DECoder<n>:SPI:CLK`. The unit answers `-113,"Undefined header"`, the meters
beep, and nothing in the tooling said a word. This check says it, for every
header of every statement of every entry.

THE TREE IS THE MODEL'S OWN. Each model folder carries `<Model>.scpi.json`
beside its table, read off that model's manual (the one SOURCES.md names):

    roots       the keywords that may start a header — the manual's top-level
                subsystems, PLUS the children of a default (bracketed) node the
                manual lets you leave out (`[SENSe:]VOLTage…` makes VOLTage a root)
    optional    the default nodes the manual brackets (`[SOURce:]`, `[:IMMediate]`),
                dropped when two paths are compared
    native      true for a box that does not speak SCPI's tree (the HP 3235's
                CLOSE/OPEN): only the roots are checked
    spellings   {"KEYWORD": "where"} — a keyword the manual itself writes with two
                short forms (Rigol: `:LA:POD<n>:THReshold` beside `:DECoder<n>:THREshold`)
    unresolved  {"verb/Name": "why"} — a header the manual does not settle. It
                is reported, never invented, and an entry here that resolves
                again fails as stale, so the list can only shrink

The table's own full-path entries then complete the tree: a header resolves when
its first keyword is one of the roots. When it does not, the check looks for the
real command it is the tail of in the same table and names it.

WHAT IT REPORTS (each a failure under --check):

    root        first keyword is not a root of this model (with the full path(s)
                it is the tail of, when the table has one: a TRUNCATED parent)
    relative    a statement after `;` with no leading `:` under a parent node —
                SCPI-99 §6.2.4 parses it under the previous header's path
                (`AM:INT:FUNC SIN;AM:INT:FREQ 5` is AM:INT:AM:INT:FREQ → -113)
    spelling    one keyword written with two different short forms in one table
                (`MARker` beside `MARKer`): one of them is not the manual's
    stale       an `unresolved` entry that resolves now, or names no entry
    tree        a table with no `<Model>.scpi.json`

AND NOTES (listed with --notes, never failing):

    duplicate   two names in one verb that send the same command, neither
                declaring `alias_of` (AUDIO.komand compares keywords as written;
                this compares them through the tree: `[SENSe:]`, short/long form)
    parameter   a `do` sending bare a node the same table only sets with a value
    returns     a query whose declared format disagrees with how its own node is set
                (an enum node answering NR3) or with another name asking the same node

    python3 _komand/scpi_paths.py            # the report
    python3 _komand/scpi_paths.py --check    # exit 1 on any finding
    python3 _komand/scpi_paths.py --json     # findings as JSON

Pure: it reads the tables and the tree files and nothing else — no bench, no
network. No model is named here; the folders are the list.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBS = ('set', 'do', 'rig', 'nab')
# Reported, never failing: a duplicate may be a deliberate second name a panel binds to, and a
# bare `do` is legal where every parameter of the node is optional (APPLy, CONFigure).
NOTES = ('duplicate', 'parameter', 'returns')
VOWELS = set('AEIOU')
_SUFFIX = re.compile(r'^(.*?)((?:<[^>]*>|\{[^}]*\}|\[[0-9|]*\]|[0-9]+)*)$')


# ── keywords ────────────────────────────────────────────────────────────────

def split_suffix(token):
    """`CHANnel<n>` → ('CHANnel', '<n>'), `DECoder1` → ('DECoder', '1'), `AM` → ('AM', '')."""
    word, suffix = _SUFFIX.match(token).groups()
    if not word:  # a bare number or placeholder
        return token, ''
    return word, suffix


def rule_short(word):
    """SCPI-99 §6.2.1 for a keyword written all in capitals: 4 letters, 3 if the 4th is a vowel."""
    w = word.upper()
    if len(w) <= 4:
        return w
    return w[:3] if w[3] in VOWELS else w[:4]


def short_of(word):
    """The short form a keyword is written with: the capitals of a mixed-case word."""
    if any(c.islower() for c in word):
        caps = ''.join(c for c in word if c.isupper() or c.isdigit())
        if caps:
            return caps
    return word.upper()


class Vocabulary:
    """Long form → short form, learned from the mixed-case keywords a model writes."""

    def __init__(self, words=()):
        self.long = {}     # 'VOLTAGE' -> {'VOLT'}
        self.shorts = set()
        for w in words:
            self.learn(w)

    def learn(self, word):
        if any(c.islower() for c in word):
            s = short_of(word)
            self.long.setdefault(word.upper(), set()).add(s)
            self.shorts.add(s)

    def key(self, word):
        """The canonical (short, upper) key of one keyword without its suffix."""
        if any(c.islower() for c in word):
            return short_of(word)
        w = word.upper()
        if w in self.long:
            return sorted(self.long[w])[0]
        if w in self.shorts:
            return w
        r = rule_short(w)
        if r in self.shorts:
            return r
        return w


# ── statements ──────────────────────────────────────────────────────────────

def statements(scpi):
    """One template → [(header, rooted, query)] per `;` statement; `*` commands are skipped."""
    out = []
    for raw in scpi.split(';'):
        s = raw.strip()
        if not s:
            continue
        head = s.split(None, 1)[0]
        # a placeholder glued to the header with no space (`DISP:TEXT"<t>"`)
        head = re.split(r'["\']', head, 1)[0]
        if head.startswith('*'):
            out.append((head, True, head.endswith('?')))
            continue
        out.append((head, head.startswith(':'), head.endswith('?')))
    return out


def keywords(header):
    return [t for t in header.lstrip(':').rstrip('?').split(':') if t]


def literals(scpi):
    """The literal arguments of a template (placeholders dropped), upper-cased."""
    lits = []
    for raw in scpi.split(';'):
        parts = raw.strip().split(None, 1)
        if len(parts) > 1:
            lits += [a.strip().upper() for a in re.split(r'[ ,]', parts[1])
                     if a.strip() and '<' not in a and '{' not in a]
        lits.append('|')
    return tuple(lits)


# ── one model ───────────────────────────────────────────────────────────────

def entries(table):
    """(verb, name, entry) for every live entry, in file order; retired ones are never sent."""
    for verb in VERBS:
        for name, e in (table.get(verb) or {}).items():
            if isinstance(e, dict) and isinstance(e.get('scpi'), str) and not e.get('retired'):
                yield verb, name, e


class Model:
    def __init__(self, table, tree):
        self.table, self.tree = table, tree or {}
        self.vocab = Vocabulary()
        for _verb, _name, e in entries(table):
            for field in ('scpi', 'scpiFast', 'scpi_fast'):
                for head, _r, _q in statements(e.get(field) or ''):
                    for tok in keywords(head):
                        self.vocab.learn(split_suffix(tok)[0])
        for w in self.tree.get('roots', []) + self.tree.get('optional', []):
            self.vocab.learn(w)
        self.roots = {self.vocab.key(split_suffix(w)[0]) for w in self.tree.get('roots', [])}
        self.optional = {self.vocab.key(w) for w in self.tree.get('optional', [])}
        self.native = bool(self.tree.get('native'))

    def path(self, header):
        """A header as a tuple of canonical keys (suffixes dropped)."""
        return tuple(self.vocab.key(split_suffix(t)[0]) for t in keywords(header))

    def node_path(self, header):
        """Like `path`, with each keyword's index kept (`CHANnel1` ≠ `CHANnel2` ≠ `CHANnel<n>`)."""
        out = []
        for t in keywords(header):
            word, suffix = split_suffix(t)
            k = self.vocab.key(word)
            if k in self.optional and not suffix:
                continue
            out.append(k + re.sub(r'<[^>]*>', '<>', suffix))
        return tuple(out)

    def bare(self, path):
        """The path with the default nodes left out — what two spellings are compared by."""
        return tuple(k for k in path if k not in self.optional)

    def resolves(self, path):
        return bool(path) and path[0] in self.roots

    def full_paths(self):
        """Every resolving statement path in the table, by bare path → the header written."""
        known = {}
        for _verb, _name, e in entries(self.table):
            for i, (head, rooted, _q) in enumerate(statements(e['scpi'])):
                # only a statement read from the root: a relative one is what is being judged
                if head.startswith('*') or (i and not rooted):
                    continue
                p = self.path(head)
                if self.resolves(p):
                    known.setdefault(self.bare(p), head.lstrip(':'))
        return known


def check_model(table, tree, rel=''):
    """Findings for one table: [{kind, where, header, message}]."""
    model = Model(table, tree)
    findings = []

    def add(kind, where, header, message):
        findings.append({'kind': kind, 'model': table.get('model', '?'), 'table': rel,
                         'where': where, 'header': header, 'message': message})

    if tree is None:
        add('tree', '', '', 'no <Model>.scpi.json beside the table — its tree is undeclared')
        return findings

    unresolved = dict(tree.get('unresolved') or {})
    known = model.full_paths()
    seen = {}
    bad_where = set()
    for verb, name, e in entries(table):
        where = f'{verb}/{name}'
        prefix = ()
        for i, (head, rooted, _q) in enumerate(statements(e['scpi'])):
            if head.startswith('*'):
                prefix = ()
                continue
            p = model.path(head)
            if model.native:
                if not model.resolves(p):
                    bad_where.add(where)
                    if where not in unresolved:
                        add('root', where, head, f'`{p[0] if p else head}` is not one of this box\'s commands')
                continue
            if i and not rooted and prefix:
                full = prefix + p
                if not _in(known, model.bare(full)) and model.resolves(p):
                    bad_where.add(where)
                    if where not in unresolved:
                        add('relative', where, head,
                            f'no leading `:` after `;` — parsed under {":".join(prefix)}: as '
                            f'{":".join(full)}; write `:{head}`')
                    prefix = p[:-1]
                    continue
                p = full
            if not model.resolves(p):
                bad_where.add(where)
                if where not in unresolved:
                    tails = sorted({h for b, h in known.items()
                                    if len(b) > len(model.bare(p)) and b[-len(model.bare(p)):] == model.bare(p)}) \
                        if model.bare(p) else []
                    if tails:
                        add('root', where, head, f'`{head}` is the tail of {", ".join("`" + t + "`" for t in tails)} '
                                                 f'— its parent was cut off (TRUNCATED)')
                    else:
                        add('root', where, head, f'`{p[0] if p else head}` is not a root of this model\'s tree')
            prefix = p[:-1]
        # duplicates: same verb, same bare paths, same literals
        heads = tuple(model.node_path(h) if not h.startswith('*') else (h.upper(),)
                      for h, _r, _q in statements(e['scpi']))
        key = (verb, heads, tuple(h.endswith('?') for h, _r, _q in statements(e['scpi'])), literals(e['scpi']))
        if key in seen and e.get('alias_of') not in seen[key]:
            add('duplicate', where, e['scpi'],
                f'sends what `{seen[key][0]}` sends — declare "alias_of": "{seen[key][0]}" or retire one')
        seen.setdefault(key, []).append(name)

    # a `do` that sends a node bare which this same table only ever SETs with a value
    set_nodes = {tuple(model.node_path(h) for h, _r, _q in statements(e['scpi']) if not h.startswith('*'))
                 for v, _n, e in entries(table) if v in ('set', 'rig')}
    for verb, name, e in entries(table):
        st = statements(e['scpi'])
        if verb == 'do' and len(st) == 1 and not st[0][0].startswith('*') \
                and len(e['scpi'].split()) == 1 \
                and (model.node_path(st[0][0]),) in set_nodes:
            add('parameter', f'do/{name}', e['scpi'],
                'a `do` with no argument on a node the table only sets with one — the unit answers -109 '
                '"Missing parameter" unless every parameter of this node is optional')

    # returns: a query's declared format against the value its own node is SET with
    want = {'enum': {'CRD', 'STR', 'BOOL', 'NR1'}, 'bool': {'BOOL', 'NR1', 'CRD'},
            'numeric': {'NR1', 'NR2', 'NR3'}, 'integer': {'NR1', 'NR3'}}
    set_kind = {}
    for v, _n, e in entries(table):
        st = statements(e['scpi'])
        kind = (e.get('arg') or {}).get('kind')
        vals = (e.get('arg') or {}).get('values') or []
        if kind == 'enum' and vals and all(re.fullmatch(r'[-+]?[0-9.]+(E[-+]?[0-9]+)?', str(x), re.I) for x in vals):
            kind = 'numeric'                 # a choice of numbers (probe ratios, 3|20|200 Hz) answers a number
        if v == 'set' and len(st) == 1 and kind in want:
            set_kind.setdefault(model.node_path(st[0][0]), (kind, _n))
    by_node = {}
    for verb, name, e in entries(table):
        st = statements(e['scpi'])
        r = e.get('returns') or {}
        if verb != 'nab' or len(st) != 1 or not r.get('type') or st[0][0].startswith('*'):
            continue
        node = model.node_path(st[0][0])
        if node in set_kind and r['type'] not in want[set_kind[node][0]]:
            add('returns', f'nab/{name}', e['scpi'],
                f'declared {r["type"]}, but `{set_kind[node][1]}` sets this node as {set_kind[node][0]} — '
                f'its answer is {"/".join(sorted(want[set_kind[node][0]]))}')
        seen_r = by_node.setdefault((node, literals(e['scpi'])), (r['type'], name))
        if seen_r[0] != r['type']:
            add('returns', f'nab/{name}', e['scpi'],
                f'declared {r["type"]}, but `{seen_r[1]}` asks the same node and declares {seen_r[0]}')

    # spelling: one long keyword, two short forms
    accepted = {w.upper() for w in tree.get('spellings') or {}}
    for long_word, shorts in sorted(model.vocab.long.items()):
        if len(shorts) > 1 and long_word not in accepted:
            add('spelling', '', long_word, f'written with short forms {sorted(shorts)} — only one is the manual\'s')

    names = {f'{v}/{n}' for v, n, _e in entries(table)}
    for where, why in unresolved.items():
        if where not in names:
            add('stale', where, '', 'listed as unresolved but no such live entry')
        elif where not in bad_where:
            add('stale', where, '', 'listed as unresolved but resolves now — drop it from `unresolved`')
    return findings


def _in(known, bare):
    return bare in known


# ── the tree ────────────────────────────────────────────────────────────────

def tree_path(komand_path):
    folder = os.path.dirname(komand_path)
    return os.path.join(folder, os.path.basename(folder) + '.scpi.json')


def check_tree(root=ROOT):
    """(tables checked, findings) over every `.komand` under root."""
    findings, n = [], 0
    for path in sorted(glob.glob(os.path.join(root, '*', '*', '*.komand'))):
        n += 1
        rel = os.path.relpath(path, root)
        with open(path, encoding='utf-8') as f:
            table = json.load(f)
        tree = None
        tp = tree_path(path)
        if os.path.isfile(tp):
            with open(tp, encoding='utf-8') as f:
                tree = json.load(f)
        findings += check_model(table, tree, rel)
    return n, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='exit 1 on any finding')
    ap.add_argument('--json', action='store_true', help='findings as JSON')
    ap.add_argument('--notes', action='store_true', help='also list the notes (duplicate, parameter, returns)')
    args = ap.parse_args(argv)
    n, findings = check_tree()
    if args.json:
        print(json.dumps(findings, indent=1, ensure_ascii=False))
    else:
        shown = [f for f in findings if args.notes or f['kind'] not in NOTES]
        for f in shown:
            print(f"{f['kind']:9} {f['model']:10} {f['where']:44} {f['message']}")
        notes = sum(1 for f in findings if f['kind'] in NOTES)
        print(f' {n} table(s) checked against their own SCPI trees; '
              f'{len(findings) - notes} finding(s), {notes} note(s){"" if args.notes else " (--notes lists them)"}.')
    failing = [f for f in findings if f['kind'] not in NOTES]
    return 1 if args.check and failing else 0


if __name__ == '__main__':
    sys.exit(main())
