#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""qualify_grab.py — run each model's GRAB on its units and prove every answer comes back.

    python3 qualify_grab.py                    # every model with a GRAB, every unit that qualified it
    python3 qualify_grab.py --model 34401A
    python3 qualify_grab.py --broker 127.0.0.1:1883

THE LAST STEP OF A GRAB (owner, 2026-11-04: "document, test, qualify, build").
compile_grab.py chose the queries each unit answered ALONE; generate_device_apis.py
stacked them into `GRAB` (and `GRAB_1…n` within the input buffer). This sends
what a reader would send — each part, or the whole GRAB when it has no parts —
to each unit's `…/Write` through the bench's VISA agent, waits for its `…/Reply`,
and counts the `;`-separated answers against the queries compiled into it. A
part qualifies when the unit answered with exactly that many values and no
error. The outcome is written back into `<Model>.qualified.json` as
`grab_qualified` — when, which unit, each part, expected vs answered — so the
library carries both the evidence and the proof.

A unit that does not answer (unplugged, busy) is recorded as such; nothing is
retried here, and nothing but queries is ever sent.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_device_apis as gen  # noqa: E402

ROOT = 'APK.audio/System/Protocols/visa/Device'
TIMEOUT_S = 60


def answers(raw):
    """The values a stacked reply carries: `;`-separated, outside quotes."""
    out, cur, quoted = [], [], False
    for ch in str(raw).strip():
        if ch == '"':
            quoted = not quoted
        if ch == ';' and not quoted:
            out.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append(''.join(cur))
    return out


def judge(expected, reply):
    """{answered, ok, error} for one part's reply envelope (None = no reply)."""
    if reply is None:
        return {'answered': 0, 'ok': False, 'error': f'no reply within {TIMEOUT_S}s'}
    if reply.get('error'):
        return {'answered': 0, 'ok': False, 'error': str(reply['error'])[:300]}
    got = len(answers(reply.get('raw', '')))
    return {'answered': got, 'ok': got == expected, 'error': None if got == expected else f'{got} answers for {expected} queries'}


def parts_of(api):
    nab = api.get('endpoints', {}).get('nab', {})
    grab = nab.get('GRAB')
    if not grab:
        return []
    names = grab['grab'].get('chunks') or ['GRAB']
    return [(n, nab[n]['scpi'], len(nab[n]['grab'].get('queries') or nab[n]['grab'].get('commands'))) for n in names]


class Bench:
    def __init__(self, host, port):
        import paho.mqtt.client as mqtt
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'qualify-grab-{os.getpid()}')
        except AttributeError:
            self.client = mqtt.Client(client_id=f'qualify-grab-{os.getpid()}')
        self.replies = {}
        self.cv = threading.Condition()
        self.client.on_message = self._on_message
        self.client.connect(host, port, 30)
        self.client.loop_start()

    def _on_message(self, _c, _u, msg):
        try:
            env = json.loads(msg.payload)
        except ValueError:
            return
        with self.cv:
            self.replies.setdefault(msg.topic, []).append(env)
            self.cv.notify_all()

    def ask(self, base, scpi):
        topic = f'{base}/Reply'
        self.client.subscribe(topic, 1)
        time.sleep(0.5)
        with self.cv:
            self.replies[topic] = []
        self.client.publish(f'{base}/Write', scpi, qos=1)
        end = time.time() + TIMEOUT_S
        with self.cv:
            while time.time() < end:
                for env in self.replies.get(topic, []):
                    if str(env.get('command', '')).strip() == scpi.strip():
                        return env
                self.cv.wait(timeout=1)
        return None


def main(argv):
    host, port = '127.0.0.1', 1883
    if '--broker' in argv:
        host, _, p = argv[argv.index('--broker') + 1].partition(':')
        port = int(p or 1883)
    only = argv[argv.index('--model') + 1] if '--model' in argv else None
    bench = Bench(host, port)
    failed = 0
    for family, folder in sorted(gen.load_families().items()):
        base_dir = os.path.join(gen.INSTRUMENTS_ROOT, folder)
        for model in sorted(os.listdir(base_dir)):
            qpath = os.path.join(base_dir, model, f'{model}.qualified.json')
            apath = os.path.join(base_dir, model, f'{model}.api.json')
            if (only and model != only) or not os.path.isfile(qpath) or not os.path.isfile(apath):
                continue
            with open(apath, encoding='utf-8') as fh:
                parts = parts_of(json.load(fh))
            with open(qpath, encoding='utf-8') as fh:
                doc = json.load(fh)
            runs = []
            for unit in doc.get('units', []):
                base = f"{ROOT}/{unit.split('/', 1)[1]}"
                results = []
                for name, scpi, expected in parts:
                    verdict = judge(expected, bench.ask(base, scpi))
                    results.append({'part': name, 'expected': expected, **verdict})
                    print(f"  {family}/{model} {unit.split('/')[-1]} {name}: "
                          f"{verdict['answered']}/{expected} {'ok' if verdict['ok'] else 'FAIL — ' + str(verdict['error'])}")
                ok = all(r['ok'] for r in results)
                failed += 0 if ok else 1
                runs.append({'unit': unit, 'when': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                             'ok': ok, 'parts': results})
            doc['grab_qualified'] = runs
            with open(qpath, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(doc, indent=2) + '\n')
    bench.client.loop_stop()
    print('all units qualified' if not failed else f'{failed} unit(s) did not qualify — see grab_qualified')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
