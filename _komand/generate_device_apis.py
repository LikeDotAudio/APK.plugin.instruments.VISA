#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""
Generate comprehensive API definition files (<Model>.api.json) for each and
every device in the APK.audio instrument library.

ONE NAME PER FILE: the spec is always <Model>.api.json and never a bare
api.json, so a path always names the instrument it belongs to.

Presents all Get, Set, Nab, Rig, and Do commands with complete SCPI, MQTT,
argument, return, and subsystem metadata.

    python3 generate_device_apis.py           # write every <Model>.api.json + ports.json
    python3 generate_device_apis.py --check   # write nothing; exit 1 if any file would
                                              # change, or the manifest and the
                                              # INSTRUMENT.* folders diverge
"""

import os
import sys
import json
import glob
from collections import OrderedDict

INSTRUMENTS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN_DEVICES_PATH = os.path.join(INSTRUMENTS_ROOT, '_komand', 'knownDevices.json')
MANIFEST_PATH = os.path.join(INSTRUMENTS_ROOT, 'manifest.json')
PORTS_PATH = os.path.join(INSTRUMENTS_ROOT, '_komand', 'ports.json')
FAMILIES_PATH = os.path.join(INSTRUMENTS_ROOT, 'families.json')

# A FAMILY'S FOLDER IS `INSTRUMENT.<Family>`; ITS NAME IS `<Family>`.
# The prefix is the directory's, and nothing else's: the device type, the MQTT
# topic, the manifest key, the `tab` and the port lane all use the bare name.
# A bare `<Family>/` folder is still read, so a tree that predates the prefix
# resolves the same way.
FAMILY_PREFIX = 'INSTRUMENT.'
# The spelling before the 2026-10 dot rename, still read so an old tree resolves.
LEGACY_FAMILY_PREFIX = 'INSTRUMENT:'


def family_name(directory_name):
    """`INSTRUMENT.DMM` -> `DMM`; a bare name is returned as it is."""
    for prefix in (FAMILY_PREFIX, LEGACY_FAMILY_PREFIX):
        if directory_name.startswith(prefix):
            return directory_name[len(prefix):]
    return directory_name


def load_families(path=FAMILIES_PATH):
    """`families.json` — {family: folder}, the resolver as data (audit #4)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return dict(json.load(f).get('families', {}))
    except (OSError, ValueError):
        return {}


def family_directory(family, root=INSTRUMENTS_ROOT):
    """The family's folder: `families.json` first, else `INSTRUMENT.<family>`
    if it exists, else `<root>/<family>` (a tree that predates the index)."""
    folder = load_families(os.path.join(root, 'families.json')).get(family)
    if folder and os.path.isdir(os.path.join(root, folder)):
        return os.path.join(root, folder)
    prefixed = os.path.join(root, FAMILY_PREFIX + family)
    return prefixed if os.path.isdir(prefixed) else os.path.join(root, family)


# The catalogue fields a `.gui` and `knownDevices.json` both carry. The `.gui`
# is the source; knownDevices.json (the *IDN? catalogue PLUGIN.VISA compiles
# in) must say the same, and --check fails when it does not (audit #2).
CATALOGUE_FIELDS = ('manufacturer', 'type', 'notes')


def catalogue_disagreements(model, gui_data, known):
    """`model.field: gui X != knownDevices Y` for every field the two disagree on."""
    out = []
    for field in CATALOGUE_FIELDS:
        if field in gui_data and field in known and gui_data[field] != known[field]:
            out.append(f"{model}.{field}: .gui {gui_data[field]!r} != knownDevices.json {known[field]!r}")
    return out


class BrokenGui(SystemExit):
    """A `<Model>.gui` that exists and does not parse: said, never skipped."""

# --------------------------------------------------------------------------
# WHERE AN INSTRUMENT'S API ANSWERS, and where it goes to find the box.
#
# Two different directions, and they are kept in two different blocks because
# confusing them is the classic way to end up dialling 5025 on the wrong side:
#
#   `service`   INBOUND.  The address THIS api answers on. A panel, the OsApi
#               or a test script connects here. One port per model, one HTTP
#               path, one websocket.
#   `transport` OUTBOUND. How the api reaches the instrument itself — VISA
#               resource templates and the well-known SCPI socket ports.
#
# THE PORT IS DERIVED, NOT STORED. family lane + position in the family's
# sorted model list, so a regeneration reproduces the same number and nothing
# has to be hand-maintained:
#
#       port = PORT_BASE + family_index * PORTS_PER_FAMILY + model_index
#
# `family_index` is the digit in front of the manifest's `tab` (Spectrum 0,
# Router 1, ... VNA 12). Until now that digit only ordered the tabs and the
# manifest said so in as many words; it is load-bearing from here and the
# manifest note has been corrected to match.
#
# THE COST OF DERIVING IT: inserting a model renumbers every model after it in
# ITS family — `_komand/ports.json` is written on every run so that shift shows
# up as a reviewable diff instead of a silent reassignment. Lanes are 100 wide
# and the fullest family (Power) holds 36, so a family overflowing its lane is
# a generation-time failure, not a collision discovered on the wire.
PORT_BASE = 15000
PORTS_PER_FAMILY = 100

# The reserved window, 15000-16299 across 13 families. Clear of everything the
# system already holds: 1883-1885 brokers, 3221 docs, 5000/5001 NMOS, 5004
# RTP-MIDI, 5007/5008 + 5101-5106 + 5201 + 5301-5306 NMOS GUI, 5024/5025 SCPI,
# 5353 mDNS, 5683 CoAP, 5959-5970 NDI, 8009 Chromecast, 8080/8081/8100 portal,
# 9000 Ember, 9001-9003 websocket listeners.

# Protocol constants for talking TO an instrument. These are facts about the
# protocols, not an inventory of which interface any given box actually has —
# a 3458A has no ethernet at all and this block still lists HiSLIP, because
# what a device answers on is measured by the discovery sweep and written to
# the probe file, never guessed here.
VISA_RESOURCE_TEMPLATES = OrderedDict([
    ("lan", "TCPIP0::<host>::inst0::INSTR"),
    ("raw", "TCPIP0::<host>::5025::SOCKET"),
    ("hislip", "TCPIP0::<host>::hislip0::INSTR"),
    ("gpib", "GPIB0::<address>::INSTR"),
    ("usb", "USB0::<vid>::<pid>::<serial>::INSTR"),
    ("serial", "ASRL<n>::INSTR"),
])

INSTRUMENT_SOCKETS = OrderedDict([
    ("raw_socket", OrderedDict([
        ("port", 5025), ("kind", "tcp"),
        ("write_terminator", "\n"), ("read_terminator", "\n"),
        ("description", "Bare SCPI over TCP. No session layer, no discovery."),
    ])),
    ("hislip", OrderedDict([
        ("port", 4880), ("kind", "tcp"),
        ("description", "IVI HiSLIP. Carries SRQ and device clear, unlike the raw socket."),
    ])),
    ("vxi11", OrderedDict([
        ("port", 111), ("kind", "tcp"),
        ("description", "SUNRPC portmapper only; the core channel port is negotiated per session."),
    ])),
    ("telnet", OrderedDict([
        ("port", 5024), ("kind", "tcp"),
        ("description", "Human-facing SCPI prompt. Echoes and prints a banner — do not parse."),
    ])),
])


def load_family_lanes():
    """Family index per class, read from the manifest's tab ordering prefix."""
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    lanes = {}
    for name, entry in manifest.items():
        if name.startswith('_'):
            continue
        tab = entry.get('tab', '')
        head = tab.split('_', 1)[0]
        if not head.isdigit():
            raise SystemExit(
                f"manifest.json: class {name!r} has tab {tab!r} with no leading index; "
                f"the port lane cannot be derived from it."
            )
        lanes[name] = int(head)
    return lanes


def build_service_block(family, model, family_index, model_index):
    """INBOUND — the address this instrument's API answers on."""
    if model_index >= PORTS_PER_FAMILY:
        raise SystemExit(
            f"{family} holds more than {PORTS_PER_FAMILY} models; {model} would "
            f"land in the next family's port lane. Widen PORTS_PER_FAMILY."
        )
    base = PORT_BASE + family_index * PORTS_PER_FAMILY

    # THE PATH SEGMENT IS SLUGGED, THE MODEL IS NOT. Three catalogue names carry
    # a space — `DS1104Z Plus`, `E36300 Series`, `8590 Series` — and a raw space
    # in a route is not a URL, it is a URL that has to be percent-encoded by
    # every caller or silently truncated by one that forgets. The underscore is
    # applied once, here, and `model` above still holds the catalogue spelling
    # so the folder is always recoverable from the document.
    seg = model.replace(' ', '_')
    path = f"/api/instrument/{family}/{seg}"
    ws_path = f"/ws/instrument/{family}/{seg}"
    slug = f"{family}.{seg}"
    return OrderedDict([
        ("host", "0.0.0.0"),
        ("port", base + model_index),
        ("family_lane", OrderedDict([
            ("family_index", family_index),
            ("base", base),
            ("offset", model_index),
        ])),
        ("path", path),
        ("routes", OrderedDict([
            ("spec", f"{path}/{seg}.api.json"),
            ("health", f"{path}/health"),
            ("get", f"{path}/get/<command>"),
            ("set", f"{path}/set/<command>"),
            ("nab", f"{path}/nab/<command>"),
            ("rig", f"{path}/rig/<command>"),
            ("do", f"{path}/do/<command>"),
        ])),
        ("socket", OrderedDict([
            ("ws", ws_path),
            ("readings", f"{ws_path}/readings"),
            ("unix", f"/run/apk/instruments/{slug}.sock"),
        ])),
    ])


def build_transport_block():
    """OUTBOUND — how this API reaches the instrument."""
    return OrderedDict([
        ("_note", "Protocol constants, not a per-model interface inventory. "
                  "Which of these a box actually answers on is measured by the "
                  "discovery sweep and recorded in the family probe file."),
        ("default", "raw_socket"),
        ("visa", VISA_RESOURCE_TEMPLATES),
        ("sockets", INSTRUMENT_SOCKETS),
    ])

# --------------------------------------------------------------------------
# WHAT THE BOX CALLS ITSELF, when that is not what this library filed it under.
#
# The folder name is a CATALOGUE spelling, chosen so a human scanning the tree
# can tell two instruments apart. `*IDN?` returns a WIRE spelling, chosen by the
# instrument's firmware in 1989. They usually agree; where they do not, the
# discovery sweep files the device under the wire spelling and nothing joins it
# to its commands.
#
# DECLARED, NOT DERIVED. A rule that strips a leading manufacturer token would
# turn `HP_8903B` into `8903B` and would also turn `Porta_one` into `one`, and
# the second mistake is silent — it would hand the Audio Precision's command set
# to anything that ever reports a model called `one`. So each alias is written
# down, one line, traceable to a bench sighting rather than to a pattern.
#
#   HP_8903B: the GPIB #28 sighting reports `8903B` with the IDN note
#             "HP 8903B Audio Distortion Analyzer".
IDN_ALIASES = {
    'HP_8903B': ['8903B'],
}

# --------------------------------------------------------------------------
# Baseline command sets and primary donors — DATA, not code (audit 2026-10-30
# #5). They were ~950 lines of Python dict literals here; they are now
# `_komand/baselines/<Family>.json` (a family with no authored .komand) and
# `_komand/baselines/donors.json` (the authored model a table-less model
# inherits from). Same content, so every generated spec is byte-identical.
# --------------------------------------------------------------------------

BASELINES_DIR = os.path.join(INSTRUMENTS_ROOT, '_komand', 'baselines')


def load_baselines(directory=BASELINES_DIR):
    """{family: baseline command set}, one `<Family>.json` each (notes dropped)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(directory, '*.json'))):
        name = os.path.splitext(os.path.basename(path))[0]
        if name == 'donors':
            continue
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f, object_pairs_hook=OrderedDict)
        out[name] = OrderedDict((k, v) for k, v in doc.items() if not k.startswith('_'))
    return out


def load_donors(directory=BASELINES_DIR):
    """{family: donor model} from `donors.json`."""
    with open(os.path.join(directory, 'donors.json'), 'r', encoding='utf-8') as f:
        return dict(json.load(f)['donors'])


BASELINE_COMMANDS = load_baselines()
PRIMARY_DONOR_MODELS = load_donors()


def load_all_authored_komands():
    """Load all existing .komand files keyed by model."""
    komands = {}
    for p in glob.glob(os.path.join(INSTRUMENTS_ROOT, '*', '*', '*.komand')):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                m = data.get('model')
                if m:
                    komands[m] = data
        except Exception as e:
            print(f"Warning: error reading {p}: {e}", file=sys.stderr)
    return komands


def command_order(item):
    """Sort key for one `(name, command)` pair in a verb bucket.

    IEEE-488.2 common commands (`*IDN?`, `*RST`, `*ESR?`…) are the special
    system commands every instrument shares, so they come first. Everything
    after them is alphabetical by SCPI, with the optional leading `:` and the
    long-form capitals ignored, so `BWIDth:VIDeo?` sorts beside `:BWIDth…`.
    The name breaks ties between commands that send the same SCPI.
    """
    name, raw_cmd = item
    scpi = raw_cmd.get('scpi', '') if isinstance(raw_cmd, dict) else ''
    scpi = scpi.lstrip(':').strip()
    return (not scpi.startswith('*'), scpi.lower(), name)


def sorted_commands(verb_cmds):
    """A verb bucket's commands in display order — see `command_order`."""
    return sorted(verb_cmds.items(), key=command_order)


def returns_one_thing(raw_cmd):
    """True when a query answers with a single value.

    The declared `returns.count` decides; with none declared, a template that
    chains more than one `?` query answers more than once.
    """
    returns = raw_cmd.get('returns') or {}
    count = returns.get('count')
    if isinstance(count, int):
        return count <= 1
    return raw_cmd.get('scpi', '').count('?') <= 1


def build_endpoint_entry(family, cmd_name, raw_cmd, verb):
    """Normalize a raw command dict into a clean API endpoint representation."""
    scpi = raw_cmd.get('scpi', '')
    scpi_fast = raw_cmd.get('scpiFast') or raw_cmd.get('scpi_fast')
    desc = raw_cmd.get('description', cmd_name.replace('_', ' '))
    sub = raw_cmd.get('subsystem', 'General')
    group = raw_cmd.get('group', sub)
    args = raw_cmd.get('args', [])
    arg = raw_cmd.get('arg') or {"kind": "none"}
    returns = raw_cmd.get('returns')
    unverified = raw_cmd.get('unverified', False)

    mqtt_info = {
        "topic": f"APK.audio/Gui/Komands/{family}/{cmd_name}",
        "direction": "in",
    }
    if verb == "set":
        mqtt_info["payload_format"] = {
            "command": cmd_name,
            "value": "<value>",
            "input_name": args[0] if args else "value"
        }
    elif verb == "rig":
        payload = {"command": cmd_name}
        for a in args:
            payload[a] = f"<{a}>"
        mqtt_info["payload_format"] = payload
    elif verb in ("nab", "do"):
        mqtt_info["payload_format"] = {"command": cmd_name}

    if verb == "nab":
        # Where KOMAND actually publishes it: readings.rs `reading_topic()` on the
        # device base VISA names (`serial_publish`), not a top-level `Device/`
        # family no grammar declares and nothing publishes (check.sh topicroots).
        mqtt_info["reading_topic"] = (
            f"APK.audio/System/Protocols/visa/Device/<type>/<model>/<dev>/Reading/{cmd_name}")
        mqtt_info["reading_direction"] = "out"

    entry = {
        "command": cmd_name,
        "verb": verb,
        "description": desc,
        "scpi": scpi,
    }
    if scpi_fast and scpi_fast != scpi:
        entry["scpi_fast"] = scpi_fast
    entry["subsystem"] = sub
    entry["group"] = group
    entry["args"] = args
    entry["arg"] = arg
    entry["returns"] = returns
    entry["mqtt"] = mqtt_info
    entry["unverified"] = unverified

    return entry


def generate_device_api(family, model, authored_komands, known_devices,
                        family_index, model_index):
    """Generate the full API dictionary for one device model."""
    gui_file = os.path.join(family_directory(family), model, f"{model}.gui")
    gui_data = {}
    if os.path.isfile(gui_file):
        # A BROKEN .gui IS AN ERROR, NOT AN ABSENT ONE (audit #3). This was
        # `except Exception: pass`: a malformed file produced a spec with the
        # fallback manufacturer and no channels/domains, and --check passed.
        try:
            with open(gui_file, 'r', encoding='utf-8') as f:
                gui_data = json.load(f)
        except (OSError, ValueError) as e:
            raise BrokenGui(f"{os.path.relpath(gui_file, INSTRUMENTS_ROOT)} does not read: {e}")
        if not isinstance(gui_data, dict):
            raise BrokenGui(f"{os.path.relpath(gui_file, INSTRUMENTS_ROOT)} is not a JSON object")

    known = known_devices.get(model, {})
    manufacturer = gui_data.get('manufacturer') or known.get('manufacturer', 'Unknown')
    notes = gui_data.get('notes') or known.get('notes', '')
    channels = gui_data.get('channels')
    domains = gui_data.get('domains')

    # Determine command source
    inherited_from = None
    if model in authored_komands:
        source_komand = authored_komands[model]
    elif family in PRIMARY_DONOR_MODELS and PRIMARY_DONOR_MODELS[family] in authored_komands:
        donor_model = PRIMARY_DONOR_MODELS[family]
        source_komand = authored_komands[donor_model]
        inherited_from = donor_model
    elif family in BASELINE_COMMANDS:
        source_komand = BASELINE_COMMANDS[family]
        inherited_from = f"{family}_Baseline"
    else:
        source_komand = {}

    endpoints = {
        "get": {},
        "set": {},
        "nab": {},
        "rig": {},
        "do": {}
    }

    # Populate endpoints for canonical verbs
    for verb in ("set", "nab", "rig", "do"):
        verb_cmds = source_komand.get(verb, {})
        for cname, raw_cmd in sorted_commands(verb_cmds):
            if not isinstance(raw_cmd, dict):
                continue
            # A retired command (the manual shows it does not exist) is not
            # published in the spec; it stays in the table with its citation.
            if raw_cmd.get('retired'):
                continue
            # A model-only command (an undocumented back door of the donor's own
            # firmware, e.g. the N9340B's :DEBug:REMote) is not a family command:
            # a model that only BORROWS the donor's table does not get it.
            if inherited_from and raw_cmd.get('model_only'):
                continue
            item = build_endpoint_entry(family, cname, raw_cmd, verb)
            endpoints[verb][cname] = item
            # A single-value NAB is also exposed under GET for REST/query
            # equivalence. Anything that returns more than one thing is a NAB
            # and only a NAB — a chained readback is not a plain GET.
            if verb == "nab" and returns_one_thing(raw_cmd):
                get_item = dict(item)
                get_item["verb"] = "get"
                endpoints["get"][cname] = get_item

    counts = {
        "total_commands": len(endpoints["set"]) + len(endpoints["nab"]) + len(endpoints["rig"]) + len(endpoints["do"]),
        "get_count": len(endpoints["get"]),
        "set_count": len(endpoints["set"]),
        "nab_count": len(endpoints["nab"]),
        "rig_count": len(endpoints["rig"]),
        "do_count": len(endpoints["do"]),
    }

    api_doc = OrderedDict([
        ("api_version", "1.0.0"),
        ("model", model),
        ("family", family),
        ("manufacturer", manufacturer),
        ("notes", notes),
    ])
    if model in IDN_ALIASES:
        api_doc["aliases"] = list(IDN_ALIASES[model])
    if channels is not None:
        api_doc["channels"] = channels
    if domains is not None:
        api_doc["domains"] = domains
    if inherited_from is not None:
        api_doc["inherited_from"] = inherited_from

    api_doc["service"] = build_service_block(family, model, family_index, model_index)
    api_doc["transport"] = build_transport_block()

    api_doc["verb_mapping"] = {
        "get": "Single-value queries (each one also a NAB)",
        "set": "Single parameter mutation and write commands",
        "nab": "Observation and telemetry acquisition queries — anything that returns more than one thing is a NAB only",
        "rig": "Multi-argument system configuration setup commands",
        "do": "Zero-argument execution actions and trigger commands",
    }
    api_doc["summary"] = counts
    api_doc["endpoints"] = endpoints

    return api_doc


def _json_text(document):
    return json.dumps(document, indent=2) + '\n'


def _emit(path, text, check, drift):
    """Write `text` to `path`, or under --check record that it would change."""
    if check:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if f.read() == text:
                    return
        except OSError:
            pass
        drift.append(os.path.relpath(path, INSTRUMENTS_ROOT))
        return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def main():
    check = '--check' in sys.argv[1:]
    # ports.json as it stood BEFORE this run, for the retirement check.
    previous = {}
    try:
        with open(PORTS_PATH, 'r', encoding='utf-8') as f:
            previous = json.load(f).get('instruments', {})
    except (OSError, ValueError):
        pass
    drift = []
    authored_komands = load_all_authored_komands()
    family_lanes = load_family_lanes()
    known_devices = {}
    if os.path.isfile(KNOWN_DEVICES_PATH):
        with open(KNOWN_DEVICES_PATH, 'r', encoding='utf-8') as f:
            known_devices = json.load(f)

    # Sorted by the BARE name, so the prefix cannot reorder the lanes.
    classes = sorted(set(
        family_name(d) for d in os.listdir(INSTRUMENTS_ROOT)
        if os.path.isdir(os.path.join(INSTRUMENTS_ROOT, d))
        and not d.startswith(('.', '_'))
        and d not in ('src', 'SRC', 'Documentation')  # crate and wiki, not classes
    ))

    missing = [c for c in classes if c not in family_lanes]
    if missing:
        raise SystemExit(
            "manifest.json declares no tab for " + ", ".join(missing) +
            " — every class needs one before a port lane can be derived."
        )
    # The other direction: a manifest class with no INSTRUMENT.<Class> folder is
    # a tab and a port lane for nothing.
    orphans = [c for c in family_lanes if c not in classes]
    if orphans:
        raise SystemExit(
            "manifest.json declares " + ", ".join(sorted(orphans)) +
            " but no INSTRUMENT.<Class> folder holds it."
        )

    generated = 0
    total_commands = 0
    allocation = OrderedDict()
    taken = {}
    swept = []

    for family in classes:
        family_dir = family_directory(family)
        devs = sorted([
            d for d in os.listdir(family_dir)
            if os.path.isdir(os.path.join(family_dir, d)) and d != 'gui'
        ])
        for model_index, model in enumerate(devs):
            model_dir = os.path.join(family_dir, model)
            api_doc = generate_device_api(
                family, model, authored_komands, known_devices,
                family_lanes[family], model_index,
            )

            service = api_doc["service"]
            port = service["port"]
            if port in taken:
                raise SystemExit(
                    f"port {port} claimed by both {taken[port]} and {family}/{model}."
                )
            taken[port] = f"{family}/{model}"
            allocation[f"{family}/{model}"] = OrderedDict([
                ("port", port),
                ("path", service["path"]),
                ("socket", service["socket"]["ws"]),
            ])

            # 1. Write <Model>.api.json
            api_file = os.path.join(model_dir, f"{model}.api.json")
            _emit(api_file, _json_text(api_doc), check, drift)

            # 2. ONE NAME PER FILE. There used to be an `api.json` symlink beside
            #    every spec pointing at `<Model>.api.json`. It is swept away here
            #    rather than merely no longer written, because the generic name
            #    is the whole problem: `SMU/2410/api.json` and
            #    `DMM/34411A/api.json` are the same string, so an open file, a
            #    grep hit and a stack trace all stopped saying WHICH instrument
            #    they meant. `<Model>.api.json` never loses that. Nothing read
            #    the symlink — it was convenience, and it cost identity.
            stale = os.path.join(model_dir, "api.json")
            if (os.path.islink(stale) or os.path.isfile(stale)) and check:
                drift.append(os.path.relpath(stale, INSTRUMENTS_ROOT))
            elif os.path.islink(stale) or os.path.isfile(stale):
                try:
                    os.remove(stale)
                    swept.append(os.path.relpath(stale, INSTRUMENTS_ROOT))
                except OSError as e:
                    print(f"Warning: could not remove {stale}: {e}", file=sys.stderr)

            generated += 1
            total_commands += api_doc["summary"]["total_commands"]

    # The allocation map, written on every run so a renumbering caused by an
    # inserted model arrives as a diff rather than as a surprise on the wire.
    ports_doc = OrderedDict([
        ("_note", "DERIVED — regenerated by _komand/generate_device_apis.py. "
                  "Do not hand-edit; change the allocator instead. "
                  "port = PORT_BASE + family_index * PORTS_PER_FAMILY + model_index."),
        ("port_base", PORT_BASE),
        ("ports_per_family", PORTS_PER_FAMILY),
        ("family_lanes", OrderedDict(
            (f, PORT_BASE + family_lanes[f] * PORTS_PER_FAMILY) for f in classes
        )),
        ("instruments", allocation),
    ])
    _emit(PORTS_PATH, _json_text(ports_doc), check, drift)

    # The resolver index must name exactly the folders on disk.
    indexed = load_families()
    on_disk = {family_name(d): d for d in os.listdir(INSTRUMENTS_ROOT)
               if os.path.isdir(os.path.join(INSTRUMENTS_ROOT, d))
               and d.startswith((FAMILY_PREFIX, LEGACY_FAMILY_PREFIX))}
    index_problems = [f"families.json: {f} -> {indexed.get(f)!r}, folder {on_disk.get(f)!r}"
                      for f in sorted(set(indexed) | set(on_disk)) if indexed.get(f) != on_disk.get(f)]

    # The catalogue fields agree between every .gui and knownDevices.json.
    disagreements = []
    for family in classes:
        family_dir = family_directory(family)
        for model in sorted(os.listdir(family_dir)):
            gui_file = os.path.join(family_dir, model, f"{model}.gui")
            if model in known_devices and os.path.isfile(gui_file):
                with open(gui_file, 'r', encoding='utf-8') as f:
                    disagreements += catalogue_disagreements(model, json.load(f), known_devices[model])

    # Every donor is an authored model of its family.
    bad_donors = [f"baselines/donors.json: {fam} -> {m} has no authored .komand"
                  for fam, m in PRIMARY_DONOR_MODELS.items() if m not in authored_komands]

    # A model that left must be retired by name, not dropped (audit #6).
    retired = {}
    try:
        with open(os.path.join(INSTRUMENTS_ROOT, '_komand', 'retired_ports.json'), 'r', encoding='utf-8') as f:
            retired = json.load(f).get('retired', {})
    except (OSError, ValueError) as e:
        print(f"Warning: _komand/retired_ports.json unreadable: {e}", file=sys.stderr)
    port_problems = [f"ports: {key} (port {entry.get('port')}) is no longer generated — list it in _komand/retired_ports.json"
                     for key, entry in previous.items() if key not in allocation and key not in retired]
    port_problems += [f"ports: retired {key}'s port {r.get('port')} is reallocated to {taken[r.get('port')]}"
                      for key, r in retired.items() if r.get('port') in taken and taken[r.get('port')] != key]

    # Every governed file against its JSON Schema (_komand/schemas/).
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import schema_check
    schema_files, schema_problems = schema_check.check_tree(INSTRUMENTS_ROOT)

    problems = index_problems + disagreements + bad_donors + port_problems + [f"schema: {p}" for p in schema_problems]
    for p in problems:
        print(f"problem: {p}", file=sys.stderr)

    if check:
        for path in drift:
            print(f"would change: {path}")
        print(f" {schema_files} file(s) checked against _komand/schemas/; "
              f"{len(problems)} catalogue/schema/index problem(s).")
        print(f" {generated} specs across {len(classes)} families checked; "
              f"{len(drift)} file(s) out of date.")
        return 1 if drift or problems else 0

    if problems:
        print(f" {len(problems)} catalogue/schema/index problem(s) — see above; --check will fail.")
    print(f" Successfully generated API specifications for {generated} devices across {len(classes)} families.")
    print(f" Total commands presented: {total_commands}")
    if taken:
        print(f" Ports allocated: {len(taken)} in {min(taken)}-{max(taken)} -> _komand/ports.json")
    if swept:
        print(f" Swept {len(swept)} stale bare api.json file(s); the spec is <Model>.api.json only.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
