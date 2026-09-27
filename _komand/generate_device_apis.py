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

# A FAMILY'S FOLDER IS `INSTRUMENT:<Family>`; ITS NAME IS `<Family>`.
# The prefix is the directory's, and nothing else's: the device type, the MQTT
# topic, the manifest key, the `tab` and the port lane all use the bare name.
# A bare `<Family>/` folder is still read, so a tree that predates the prefix
# resolves the same way.
FAMILY_PREFIX = 'INSTRUMENT:'


def family_name(directory_name):
    """`INSTRUMENT:DMM` -> `DMM`; a bare name is returned as it is."""
    if directory_name.startswith(FAMILY_PREFIX):
        return directory_name[len(FAMILY_PREFIX):]
    return directory_name


def family_directory(family, root=INSTRUMENTS_ROOT):
    """`<root>/INSTRUMENT:<family>` if it exists, else `<root>/<family>`."""
    prefixed = os.path.join(root, FAMILY_PREFIX + family)
    return prefixed if os.path.isdir(prefixed) else os.path.join(root, family)

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
# Baseline command sets for families without authored .komand tables
# --------------------------------------------------------------------------

BASELINE_COMMANDS = {
    "Counter": {
        "set": {
            "Set_Frequency_Arm_Start": {
                "scpi": ":SENSe:FREQuency:ARM:STARt:SOURce <source>",
                "scpi_fast": ":SENS:FREQ:ARM:STAR:SOUR <source>",
                "description": "Set start arm source for frequency measurements",
                "subsystem": "SENSe",
                "group": "Arming and Triggering",
                "args": ["source"],
                "arg": {"kind": "enum", "values": ["IMMediate", "EXTernal"]},
            },
            "Set_Gate_Time": {
                "scpi": ":SENSe:FREQuency:ARM:STOP:TIMer <seconds>",
                "scpi_fast": ":SENS:FREQ:ARM:STOP:TIM <seconds>",
                "description": "Set gate time in seconds",
                "subsystem": "SENSe",
                "group": "Gate Control",
                "args": ["seconds"],
                "arg": {"kind": "numeric", "unit": "s", "min": 0.001, "max": 100.0},
            },
            "Set_Input1_Coupling": {
                "scpi": ":INPut1:COUPling <coupling>",
                "scpi_fast": ":INP1:COUP <coupling>",
                "description": "Set Channel 1 AC/DC input coupling",
                "subsystem": "INPut",
                "group": "Input Conditioning",
                "args": ["coupling"],
                "arg": {"kind": "enum", "values": ["AC", "DC"]},
            },
            "Set_Input1_Impedance": {
                "scpi": ":INPut1:IMPedance <ohms>",
                "scpi_fast": ":INP1:IMP <ohms>",
                "description": "Set Channel 1 input impedance (50 Ohm or 1 MOhm)",
                "subsystem": "INPut",
                "group": "Input Conditioning",
                "args": ["ohms"],
                "arg": {"kind": "enum", "values": ["50", "1M"]},
            },
            "Set_Input1_Filter": {
                "scpi": ":INPut1:FILTer:STATe <state>",
                "scpi_fast": ":INP1:FILT:STAT <state>",
                "description": "Enable or disable 100 kHz low-pass filter on Channel 1",
                "subsystem": "INPut",
                "group": "Input Conditioning",
                "args": ["state"],
                "arg": {"kind": "bool", "values": ["OFF", "ON"]},
            },
            "Set_Input2_Coupling": {
                "scpi": ":INPut2:COUPling <coupling>",
                "scpi_fast": ":INP2:COUP <coupling>",
                "description": "Set Channel 2 AC/DC input coupling",
                "subsystem": "INPut",
                "group": "Input Conditioning",
                "args": ["coupling"],
                "arg": {"kind": "enum", "values": ["AC", "DC"]},
            },
            "Set_Input2_Impedance": {
                "scpi": ":INPut2:IMPedance <ohms>",
                "scpi_fast": ":INP2:IMP <ohms>",
                "description": "Set Channel 2 input impedance (50 Ohm or 1 MOhm)",
                "subsystem": "INPut",
                "group": "Input Conditioning",
                "args": ["ohms"],
                "arg": {"kind": "enum", "values": ["50", "1M"]},
            },
            "Set_Trigger_Level": {
                "scpi": ":SENSe:EVENt1:LEVel <level>",
                "scpi_fast": ":SENS:EVEN1:LEV <level>",
                "description": "Set Channel 1 trigger threshold voltage",
                "subsystem": "SENSe",
                "group": "Trigger Setup",
                "args": ["level"],
                "arg": {"kind": "numeric", "unit": "V"},
            },
            "Set_Function": {
                "scpi": ":SENSe:FUNCtion '<function>'",
                "scpi_fast": ":SENS:FUNC '<function>'",
                "description": "Set active measurement function",
                "subsystem": "SENSe",
                "group": "Measurement Setup",
                "args": ["function"],
                "arg": {"kind": "enum", "values": ["FREQuency 1", "PERiod 1", "TINTerval 1,2", "PWIDth 1", "NWIDth 1"]},
            },
        },
        "nab": {
            "Read_Next": {
                "scpi": ":READ?",
                "scpi_fast": ":READ?",
                "description": "Trigger counter and fetch next reading",
                "subsystem": "SENSe",
                "group": "Data Acquisition",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"separator": ";", "fields": [{"name": "reading", "unit": "Hz"}], "unit": "Hz"},
            },
            "Fetch_Data": {
                "scpi": ":FETCh?",
                "scpi_fast": ":FETC?",
                "description": "Fetch last calculated measurement",
                "subsystem": "SENSe",
                "group": "Data Acquisition",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"separator": ";", "fields": [{"name": "reading", "unit": "Hz"}], "unit": "Hz"},
            },
            "Measure_Frequency": {
                "scpi": ":MEASure:FREQuency?",
                "scpi_fast": ":MEAS:FREQ?",
                "description": "Measure frequency on channel 1",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"fields": [{"name": "frequency", "unit": "Hz"}], "unit": "Hz"},
            },
            "Measure_Period": {
                "scpi": ":MEASure:PERiod?",
                "scpi_fast": ":MEAS:PER?",
                "description": "Measure signal period on channel 1",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"fields": [{"name": "period", "unit": "s"}], "unit": "s"},
            },
            "Measure_Time_Interval": {
                "scpi": ":MEASure:TINTerval?",
                "scpi_fast": ":MEAS:TINT?",
                "description": "Measure time interval between channel 1 and channel 2",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"fields": [{"name": "interval", "unit": "s"}], "unit": "s"},
            },
            "Measure_Pulse_Width": {
                "scpi": ":MEASure:PWIDth?",
                "scpi_fast": ":MEAS:PWID?",
                "description": "Measure positive pulse width",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"fields": [{"name": "width", "unit": "s"}], "unit": "s"},
            },
            "Read_IDN": {
                "scpi": "*IDN?",
                "scpi_fast": "*IDN?",
                "description": "Read instrument identification string",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"separator": ",", "fields": [{"name": "manufacturer"}, {"name": "model"}, {"name": "serial"}, {"name": "firmware"}]},
            },
            "Query_Error": {
                "scpi": ":SYSTem:ERRor?",
                "scpi_fast": ":SYST:ERR?",
                "description": "Query next error code and message from queue",
                "subsystem": "SYSTem",
                "group": "System Utilities",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"separator": ",", "fields": [{"name": "code"}, {"name": "message"}]},
            },
            "Query_OPC": {
                "scpi": "*OPC?",
                "scpi_fast": "*OPC?",
                "description": "Query operation complete state",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"fields": [{"name": "complete"}]},
            },
            "Read_STB": {
                "scpi": "*STB?",
                "scpi_fast": "*STB?",
                "description": "Read status byte register",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"fields": [{"name": "status_byte"}]},
            },
        },
        "do": {
            "Reset": {
                "scpi": "*RST",
                "scpi_fast": "*RST",
                "description": "Reset counter to factory default settings",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Clear_Status": {
                "scpi": "*CLS",
                "scpi_fast": "*CLS",
                "description": "Clear status registers and error queue",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Initiate": {
                "scpi": ":INITiate",
                "scpi_fast": ":INIT",
                "description": "Initiate measurement cycle",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Abort": {
                "scpi": ":ABORt",
                "scpi_fast": ":ABOR",
                "description": "Abort active measurement",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Auto_Trigger": {
                "scpi": ":SENSe:EVENt1:LEVel:AUTO ON",
                "scpi_fast": ":SENS:EVEN1:LEV:AUTO ON",
                "description": "Automatically set trigger levels",
                "subsystem": "SENSe",
                "group": "Trigger Setup",
                "args": [],
            },
        },
        "rig": {
            "Configure_Frequency": {
                "scpi": ":CONFigure:FREQuency <expected_freq>, <resolution>",
                "scpi_fast": ":CONF:FREQ <expected_freq>, <resolution>",
                "description": "Configure frequency measurement with expected frequency and target resolution",
                "subsystem": "CONFigure",
                "group": "Measurement Configuration",
                "args": ["expected_freq", "resolution"],
                "arg": {
                    "kind": "multi",
                    "parameters": {
                        "expected_freq": {"kind": "numeric", "unit": "Hz"},
                        "resolution": {"kind": "numeric", "unit": "Hz"},
                    },
                },
            },
            "Configure_Period": {
                "scpi": ":CONFigure:PERiod <expected_period>, <resolution>",
                "scpi_fast": ":CONF:PER <expected_period>, <resolution>",
                "description": "Configure period measurement with expected period and resolution",
                "subsystem": "CONFigure",
                "group": "Measurement Configuration",
                "args": ["expected_period", "resolution"],
                "arg": {
                    "kind": "multi",
                    "parameters": {
                        "expected_period": {"kind": "numeric", "unit": "s"},
                        "resolution": {"kind": "numeric", "unit": "s"},
                    },
                },
            },
            "Configure_Time_Interval": {
                "scpi": ":CONFigure:TINTerval",
                "scpi_fast": ":CONF:TINT",
                "description": "Configure time interval measurement between Channel 1 and 2",
                "subsystem": "CONFigure",
                "group": "Measurement Configuration",
                "args": [],
            },
        },
    },

    "DAQ": {
        "set": {
            "Set_Scan_List": {
                "scpi": ":ROUTe:SCAN (@<channels>)",
                "scpi_fast": ":ROUT:SCAN (@<channels>)",
                "description": "Define channels included in automatic scan sweep",
                "subsystem": "ROUTe",
                "group": "Route Configuration",
                "args": ["channels"],
                "arg": {"kind": "string"},
            },
            "Set_Scan_Interval": {
                "scpi": ":ROUTe:SCAN:TIMer <seconds>",
                "scpi_fast": ":ROUT:SCAN:TIM <seconds>",
                "description": "Set timer interval between scan sweeps",
                "subsystem": "ROUTe",
                "group": "Scan Timing",
                "args": ["seconds"],
                "arg": {"kind": "numeric", "unit": "s", "min": 0.0, "max": 359999.0},
            },
            "Set_Channel_Delay": {
                "scpi": ":ROUTe:CHANnel:DELay <seconds>, (@<channels>)",
                "scpi_fast": ":ROUT:CHAN:DEL <seconds>, (@<channels>)",
                "description": "Set settling delay time before measurement on specified channels",
                "subsystem": "ROUTe",
                "group": "Scan Timing",
                "args": ["seconds", "channels"],
            },
            "Set_Monitor_Channel": {
                "scpi": ":ROUTe:MONItor (@<channel>)",
                "scpi_fast": ":ROUT:MON (@<channel>)",
                "description": "Designate single channel for real-time monitoring",
                "subsystem": "ROUTe",
                "group": "Channel Monitor",
                "args": ["channel"],
            },
            "Set_Monitor_State": {
                "scpi": ":ROUTe:MONItor:STATe <state>",
                "scpi_fast": ":ROUT:MON:STAT <state>",
                "description": "Enable or disable background channel monitoring",
                "subsystem": "ROUTe",
                "group": "Channel Monitor",
                "args": ["state"],
                "arg": {"kind": "bool", "values": ["OFF", "ON"]},
            },
            "Set_Trigger_Source": {
                "scpi": ":TRIGger:SOURce <source>",
                "scpi_fast": ":TRIG:SOUR <source>",
                "description": "Set trigger source for scan acquisition",
                "subsystem": "TRIGger",
                "group": "Trigger Setup",
                "args": ["source"],
                "arg": {"kind": "enum", "values": ["IMMediate", "TIMer", "EXTernal", "BUS", "ALARm1", "ALARm2"]},
            },
            "Set_Trigger_Count": {
                "scpi": ":TRIGger:COUNt <count>",
                "scpi_fast": ":TRIG:COUN <count>",
                "description": "Set number of sweeps to perform before trigger system idles",
                "subsystem": "TRIGger",
                "group": "Trigger Setup",
                "args": ["count"],
                "arg": {"kind": "numeric", "min": 1, "max": 50000},
            },
            "Set_Integration_NPLC": {
                "scpi": ":SENSe:VOLTage:DC:NPLC <nplc>, (@<channels>)",
                "scpi_fast": ":SENS:VOLT:DC:NPLC <nplc>, (@<channels>)",
                "description": "Set integration time in power line cycles for DC measurements",
                "subsystem": "SENSe",
                "group": "Measurement Parameters",
                "args": ["nplc", "channels"],
            },
        },
        "nab": {
            "Read_Next": {
                "scpi": ":READ?",
                "scpi_fast": ":READ?",
                "description": "Trigger scan sweep and return all channel readings",
                "subsystem": "SENSe",
                "group": "Data Acquisition",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"separator": ",", "fields": [{"name": "readings"}]},
            },
            "Fetch_Scan": {
                "scpi": ":FETCh?",
                "scpi_fast": ":FETC?",
                "description": "Fetch reading buffer contents from memory",
                "subsystem": "SENSe",
                "group": "Data Acquisition",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {"separator": ",", "fields": [{"name": "readings"}]},
            },
            "Read_Scan_List": {
                "scpi": ":ROUTe:SCAN?",
                "scpi_fast": ":ROUT:SCAN?",
                "description": "Query configured scan channel list",
                "subsystem": "ROUTe",
                "group": "Route Configuration",
                "args": [],
                "returns": {"fields": [{"name": "scan_list"}]},
            },
            "Read_Monitor_Data": {
                "scpi": ":ROUTe:MONItor:DATA?",
                "scpi_fast": ":ROUT:MON:DATA?",
                "description": "Read latest measurement from monitored channel",
                "subsystem": "ROUTe",
                "group": "Channel Monitor",
                "args": [],
                "returns": {"fields": [{"name": "reading"}]},
            },
            "Read_IDN": {
                "scpi": "*IDN?",
                "scpi_fast": "*IDN?",
                "description": "Read DAQ identity and installed module firmware",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "manufacturer"}, {"name": "model"}, {"name": "serial"}, {"name": "firmware"}]},
            },
            "Query_Error": {
                "scpi": ":SYSTem:ERRor?",
                "scpi_fast": ":SYST:ERR?",
                "description": "Query next error code and message",
                "subsystem": "SYSTem",
                "group": "System Utilities",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "code"}, {"name": "message"}]},
            },
            "Query_Scan_Size": {
                "scpi": ":DATA:POINts?",
                "scpi_fast": ":DATA:POIN?",
                "description": "Query number of readings currently stored in volatile memory",
                "subsystem": "DATA",
                "group": "Memory System",
                "args": [],
                "returns": {"fields": [{"name": "count"}]},
            },
        },
        "do": {
            "Start_Scan": {
                "scpi": ":INITiate",
                "scpi_fast": ":INIT",
                "description": "Initiate scan sequence",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Abort": {
                "scpi": ":ABORt",
                "scpi_fast": ":ABOR",
                "description": "Abort running scan sweep",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Reset": {
                "scpi": "*RST",
                "scpi_fast": "*RST",
                "description": "Reset DAQ mainframe and installed modules",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Clear_Status": {
                "scpi": "*CLS",
                "scpi_fast": "*CLS",
                "description": "Clear all status registers and error queue",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Open_All": {
                "scpi": ":ROUTe:OPEN:ALL",
                "scpi_fast": ":ROUT:OPEN:ALL",
                "description": "Open all switch and multiplexer channels across all slots",
                "subsystem": "ROUTe",
                "group": "Route Configuration",
                "args": [],
            },
            "Clear_Memory": {
                "scpi": ":DATA:CLEar",
                "scpi_fast": ":DATA:CLE",
                "description": "Clear internal reading storage buffer",
                "subsystem": "DATA",
                "group": "Memory System",
                "args": [],
            },
        },
        "rig": {
            "Configure_Voltage_Scan": {
                "scpi": ":CONFigure:VOLTage:DC <range>, <resolution>, (@<channels>)",
                "scpi_fast": ":CONF:VOLT:DC <range>, <resolution>, (@<channels>)",
                "description": "Configure DC voltage measurements with range and resolution across channel list",
                "subsystem": "CONFigure",
                "group": "Measurement Configuration",
                "args": ["range", "resolution", "channels"],
            },
            "Configure_Temperature_Scan": {
                "scpi": ":CONFigure:TEMPerature <type>, <transducer>, (@<channels>)",
                "scpi_fast": ":CONF:TEMP <type>, <transducer>, (@<channels>)",
                "description": "Configure thermocouple/RTD temperature measurement on channel list",
                "subsystem": "CONFigure",
                "group": "Measurement Configuration",
                "args": ["type", "transducer", "channels"],
            },
        },
    },

    "SMU": {
        "set": {
            "Set_Source_Function": {
                "scpi": ":SOURce:FUNCtion <func>",
                "scpi_fast": ":SOUR:FUNC <func>",
                "description": "Set active source mode: Voltage or Current",
                "subsystem": "SOURce",
                "group": "Source Setup",
                "args": ["func"],
                "arg": {"kind": "enum", "values": ["VOLTage", "CURRent"]},
            },
            "Set_Source_Voltage": {
                "scpi": ":SOURce:VOLTage:LEVel <volts>",
                "scpi_fast": ":SOUR:VOLT:LEV <volts>",
                "description": "Set voltage output level in Volts",
                "subsystem": "SOURce",
                "group": "Source Setup",
                "args": ["volts"],
                "arg": {"kind": "numeric", "unit": "V"},
            },
            "Set_Source_Current": {
                "scpi": ":SOURce:CURRent:LEVel <amps>",
                "scpi_fast": ":SOUR:CURR:LEV <amps>",
                "description": "Set current output level in Amperes",
                "subsystem": "SOURce",
                "group": "Source Setup",
                "args": ["amps"],
                "arg": {"kind": "numeric", "unit": "A"},
            },
            "Set_Voltage_Compliance": {
                "scpi": ":SENSe:VOLTage:PROTection:LEVel <volts>",
                "scpi_fast": ":SENS:VOLT:PROT:LEV <volts>",
                "description": "Set maximum voltage compliance protection limit",
                "subsystem": "SENSe",
                "group": "Compliance Limits",
                "args": ["volts"],
                "arg": {"kind": "numeric", "unit": "V"},
            },
            "Set_Current_Compliance": {
                "scpi": ":SENSe:CURRent:PROTection:LEVel <amps>",
                "scpi_fast": ":SENS:CURR:PROT:LEV <amps>",
                "description": "Set maximum current compliance protection limit",
                "subsystem": "SENSe",
                "group": "Compliance Limits",
                "args": ["amps"],
                "arg": {"kind": "numeric", "unit": "A"},
            },
            "Set_Output_State": {
                "scpi": ":OUTPut:STATe <state>",
                "scpi_fast": ":OUTP:STAT <state>",
                "description": "Turn SMU output terminal ON or OFF",
                "subsystem": "OUTPut",
                "group": "Output Control",
                "args": ["state"],
                "arg": {"kind": "bool", "values": ["OFF", "ON"]},
            },
            "Set_Sense_Function": {
                "scpi": ":SENSe:FUNCtion '<function>'",
                "scpi_fast": ":SENS:FUNC '<function>'",
                "description": "Set measurement sense mode",
                "subsystem": "SENSe",
                "group": "Measurement Setup",
                "args": ["function"],
                "arg": {"kind": "enum", "values": ["VOLTage", "CURRent", "RESistance"]},
            },
            "Set_Sense_Remote": {
                "scpi": ":SENSe:REMote <state>",
                "scpi_fast": ":SENS:REM <state>",
                "description": "Select 4-wire remote sensing or 2-wire local sensing",
                "subsystem": "SENSe",
                "group": "Measurement Setup",
                "args": ["state"],
                "arg": {"kind": "bool", "values": ["OFF", "ON"]},
            },
            "Set_Integration_NPLC": {
                "scpi": ":SENSe:NPLC <nplc>",
                "scpi_fast": ":SENS:NPLC <nplc>",
                "description": "Set A/D converter integration time in power line cycles",
                "subsystem": "SENSe",
                "group": "Measurement Setup",
                "args": ["nplc"],
                "arg": {"kind": "numeric", "min": 0.01, "max": 10.0},
            },
        },
        "nab": {
            "Read_Next": {
                "scpi": ":READ?",
                "scpi_fast": ":READ?",
                "description": "Trigger measurement and return voltage, current, and resistance",
                "subsystem": "SENSe",
                "group": "Data Acquisition",
                "args": [],
                "arg": {"kind": "none"},
                "returns": {
                    "separator": ",",
                    "fields": [
                        {"name": "voltage", "unit": "V"},
                        {"name": "current", "unit": "A"},
                        {"name": "resistance", "unit": "Ohm"},
                        {"name": "time", "unit": "s"},
                        {"name": "status"},
                    ],
                },
            },
            "Measure_Voltage": {
                "scpi": ":MEASure:VOLTage?",
                "scpi_fast": ":MEAS:VOLT?",
                "description": "Measure voltage at terminals",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "returns": {"fields": [{"name": "voltage", "unit": "V"}], "unit": "V"},
            },
            "Measure_Current": {
                "scpi": ":MEASure:CURRent?",
                "scpi_fast": ":MEAS:CURR?",
                "description": "Measure current flowing through terminals",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "returns": {"fields": [{"name": "current", "unit": "A"}], "unit": "A"},
            },
            "Measure_Resistance": {
                "scpi": ":MEASure:RESistance?",
                "scpi_fast": ":MEAS:RES?",
                "description": "Calculate resistance from measured V and I",
                "subsystem": "SENSe",
                "group": "Direct Measurement",
                "args": [],
                "returns": {"fields": [{"name": "resistance", "unit": "Ohm"}], "unit": "Ohm"},
            },
            "Read_Output_State": {
                "scpi": ":OUTPut:STATe?",
                "scpi_fast": ":OUTP:STAT?",
                "description": "Query output enabled/disabled status",
                "subsystem": "OUTPut",
                "group": "Output Control",
                "args": [],
                "returns": {"fields": [{"name": "state"}]},
            },
            "Read_Compliance_Status": {
                "scpi": ":SENSe:PROTection:TRIPped?",
                "scpi_fast": ":SENS:PROT:TRIP?",
                "description": "Check if voltage or current compliance threshold was tripped",
                "subsystem": "SENSe",
                "group": "Compliance Limits",
                "args": [],
                "returns": {"fields": [{"name": "tripped"}]},
            },
            "Read_IDN": {
                "scpi": "*IDN?",
                "scpi_fast": "*IDN?",
                "description": "Read SMU identification string",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "manufacturer"}, {"name": "model"}, {"name": "serial"}, {"name": "firmware"}]},
            },
            "Query_Error": {
                "scpi": ":SYSTem:ERRor?",
                "scpi_fast": ":SYST:ERR?",
                "description": "Query system error queue",
                "subsystem": "SYSTem",
                "group": "System Utilities",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "code"}, {"name": "message"}]},
            },
        },
        "do": {
            "Output_ON": {
                "scpi": ":OUTPut:STATe ON",
                "scpi_fast": ":OUTP:STAT ON",
                "description": "Enable SMU power output terminals",
                "subsystem": "OUTPut",
                "group": "Output Control",
                "args": [],
            },
            "Output_OFF": {
                "scpi": ":OUTPut:STATe OFF",
                "scpi_fast": ":OUTP:STAT OFF",
                "description": "Safely disable SMU output terminals",
                "subsystem": "OUTPut",
                "group": "Output Control",
                "args": [],
            },
            "Reset": {
                "scpi": "*RST",
                "scpi_fast": "*RST",
                "description": "Reset SMU to default factory parameters",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Clear_Status": {
                "scpi": "*CLS",
                "scpi_fast": "*CLS",
                "description": "Clear status registers and error queue",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Initiate": {
                "scpi": ":INITiate",
                "scpi_fast": ":INIT",
                "description": "Arm trigger system and initiate measurement",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Abort": {
                "scpi": ":ABORt",
                "scpi_fast": ":ABOR",
                "description": "Abort ongoing sweep or measurement sequence",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
        },
        "rig": {
            "Configure_Voltage_Source": {
                "scpi": ":SOURce:FUNCtion VOLTage;:SOURce:VOLTage:LEVel <volts>;:SENSe:CURRent:PROTection <compliance>",
                "scpi_fast": ":SOUR:FUNC VOLT;:SOUR:VOLT:LEV <volts>;:SENS:CURR:PROT <compliance>",
                "description": "Configure SMU as voltage source with voltage setpoint and current compliance limit",
                "subsystem": "SOURce",
                "group": "Source Setup",
                "args": ["volts", "compliance"],
                "arg": {
                    "kind": "multi",
                    "parameters": {
                        "volts": {"kind": "numeric", "unit": "V"},
                        "compliance": {"kind": "numeric", "unit": "A"},
                    },
                },
            },
            "Configure_Current_Source": {
                "scpi": ":SOURce:FUNCtion CURRent;:SOURce:CURRent:LEVel <amps>;:SENSe:VOLTage:PROTection <compliance>",
                "scpi_fast": ":SOUR:FUNC CURR;:SOUR:CURR:LEV <amps>;:SENS:VOLT:PROT <compliance>",
                "description": "Configure SMU as current source with current setpoint and voltage compliance limit",
                "subsystem": "SOURce",
                "group": "Source Setup",
                "args": ["amps", "compliance"],
                "arg": {
                    "kind": "multi",
                    "parameters": {
                        "amps": {"kind": "numeric", "unit": "A"},
                        "compliance": {"kind": "numeric", "unit": "V"},
                    },
                },
            },
        },
    },

    "VNA": {
        "set": {
            "Set_Start_Frequency": {
                "scpi": ":SENSe:FREQuency:STARt <freq>",
                "scpi_fast": ":SENS:FREQ:STAR <freq>",
                "description": "Set sweep start frequency in Hz",
                "subsystem": "SENSe",
                "group": "Frequency Setup",
                "args": ["freq"],
                "arg": {"kind": "numeric", "unit": "Hz"},
            },
            "Set_Stop_Frequency": {
                "scpi": ":SENSe:FREQuency:STOP <freq>",
                "scpi_fast": ":SENS:FREQ:STOP <freq>",
                "description": "Set sweep stop frequency in Hz",
                "subsystem": "SENSe",
                "group": "Frequency Setup",
                "args": ["freq"],
                "arg": {"kind": "numeric", "unit": "Hz"},
            },
            "Set_Center_Frequency": {
                "scpi": ":SENSe:FREQuency:CENTer <freq>",
                "scpi_fast": ":SENS:FREQ:CENT <freq>",
                "description": "Set sweep center frequency in Hz",
                "subsystem": "SENSe",
                "group": "Frequency Setup",
                "args": ["freq"],
                "arg": {"kind": "numeric", "unit": "Hz"},
            },
            "Set_Frequency_Span": {
                "scpi": ":SENSe:FREQuency:SPAN <span>",
                "scpi_fast": ":SENS:FREQ:SPAN <span>",
                "description": "Set sweep frequency span in Hz",
                "subsystem": "SENSe",
                "group": "Frequency Setup",
                "args": ["span"],
                "arg": {"kind": "numeric", "unit": "Hz"},
            },
            "Set_Sweep_Points": {
                "scpi": ":SENSe:SWEep:POINts <points>",
                "scpi_fast": ":SENS:SWE:POIN <points>",
                "description": "Set number of measurement points per sweep",
                "subsystem": "SENSe",
                "group": "Sweep Control",
                "args": ["points"],
                "arg": {"kind": "numeric", "min": 2, "max": 100001},
            },
            "Set_IF_Bandwidth": {
                "scpi": ":SENSe:BANDwidth:RESolution <bandwidth>",
                "scpi_fast": ":SENS:BAND:RES <bandwidth>",
                "description": "Set intermediate frequency (IF) filter resolution bandwidth",
                "subsystem": "SENSe",
                "group": "Receiver Setup",
                "args": ["bandwidth"],
                "arg": {"kind": "numeric", "unit": "Hz"},
            },
            "Set_Power_Level": {
                "scpi": ":SOURce:POWer:LEVel:IMMediate:AMPLitude <power>",
                "scpi_fast": ":SOUR:POW:LEV:IMM:AMPL <power>",
                "description": "Set RF test port stimulus power level in dBm",
                "subsystem": "SOURce",
                "group": "Source Setup",
                "args": ["power"],
                "arg": {"kind": "numeric", "unit": "dBm"},
            },
            "Set_Measurement_Parameter": {
                "scpi": ":CALCulate:PARameter:DEFine '<param>'",
                "scpi_fast": ":CALC:PAR:DEF '<param>'",
                "description": "Select S-parameter to measure on active trace",
                "subsystem": "CALCulate",
                "group": "Trace Setup",
                "args": ["param"],
                "arg": {"kind": "enum", "values": ["S11", "S21", "S12", "S22"]},
            },
            "Set_Display_Format": {
                "scpi": ":CALCulate:FORMat <format>",
                "scpi_fast": ":CALC:FORM <format>",
                "description": "Set active trace display format",
                "subsystem": "CALCulate",
                "group": "Trace Setup",
                "args": ["format"],
                "arg": {"kind": "enum", "values": ["MLOGarithmic", "PHASe", "GDELay", "SMITh", "POLar", "SWR", "REAL", "IMAGinary"]},
            },
        },
        "nab": {
            "Read_S_Parameter_Data": {
                "scpi": ":CALCulate:DATA? FDATA",
                "scpi_fast": ":CALC:DATA? FDATA",
                "description": "Fetch formatted trace data points for active S-parameter",
                "subsystem": "CALCulate",
                "group": "Trace Data",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "trace_points"}]},
            },
            "Read_Frequency_Range": {
                "scpi": ":SENSe:FREQuency:STARt?;:SENSe:FREQuency:STOP?",
                "scpi_fast": ":SENS:FREQ:STAR?;:SENS:FREQ:STOP?",
                "description": "Read sweep start and stop frequency bounds",
                "subsystem": "SENSe",
                "group": "Frequency Setup",
                "args": [],
                "returns": {"separator": ";", "fields": [{"name": "start_frequency", "unit": "Hz"}, {"name": "stop_frequency", "unit": "Hz"}]},
            },
            "Read_Sweep_Time": {
                "scpi": ":SENSe:SWEep:TIME?",
                "scpi_fast": ":SENS:SWE:TIME?",
                "description": "Read calculated duration of single sweep",
                "subsystem": "SENSe",
                "group": "Sweep Control",
                "args": [],
                "returns": {"fields": [{"name": "time", "unit": "s"}], "unit": "s"},
            },
            "Read_Active_Parameter": {
                "scpi": ":CALCulate:PARameter:SELect?",
                "scpi_fast": ":CALC:PAR:SEL?",
                "description": "Query currently selected S-parameter definition",
                "subsystem": "CALCulate",
                "group": "Trace Setup",
                "args": [],
                "returns": {"fields": [{"name": "parameter"}]},
            },
            "Read_IDN": {
                "scpi": "*IDN?",
                "scpi_fast": "*IDN?",
                "description": "Read VNA identification string",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "manufacturer"}, {"name": "model"}, {"name": "serial"}, {"name": "firmware"}]},
            },
            "Query_Error": {
                "scpi": ":SYSTem:ERRor?",
                "scpi_fast": ":SYST:ERR?",
                "description": "Query system error queue",
                "subsystem": "SYSTem",
                "group": "System Utilities",
                "args": [],
                "returns": {"separator": ",", "fields": [{"name": "code"}, {"name": "message"}]},
            },
        },
        "do": {
            "Reset": {
                "scpi": "*RST",
                "scpi_fast": "*RST",
                "description": "Reset VNA to factory preset state",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Clear_Status": {
                "scpi": "*CLS",
                "scpi_fast": "*CLS",
                "description": "Clear status registers",
                "subsystem": "Common",
                "group": "IEEE 488.2 Common",
                "args": [],
            },
            "Trigger_Single": {
                "scpi": ":INITiate:CONTinuous OFF;:INITiate:IMMediate",
                "scpi_fast": ":INIT:CONT OFF;:INIT:IMM",
                "description": "Disarm continuous trigger and initiate single sweep",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Continuous_Sweep": {
                "scpi": ":INITiate:CONTinuous ON",
                "scpi_fast": ":INIT:CONT ON",
                "description": "Arm continuous sweeping mode",
                "subsystem": "TRIGger",
                "group": "Trigger System",
                "args": [],
            },
            "Autoscale": {
                "scpi": ":DISPlay:WINDow:TRACe:Y:SCALe:AUTO",
                "scpi_fast": ":DISP:WIND:TRAC:Y:SCAL:AUTO",
                "description": "Autoscale active trace Y-axis limits",
                "subsystem": "DISPlay",
                "group": "Display Format",
                "args": [],
            },
            "RF_Power_ON": {
                "scpi": ":OUTPut:STATe ON",
                "scpi_fast": ":OUTP:STAT ON",
                "description": "Turn RF stimulus port power ON",
                "subsystem": "OUTPut",
                "group": "Source Setup",
                "args": [],
            },
            "RF_Power_OFF": {
                "scpi": ":OUTPut:STATe OFF",
                "scpi_fast": ":OUTP:STAT OFF",
                "description": "Turn RF stimulus port power OFF",
                "subsystem": "OUTPut",
                "group": "Source Setup",
                "args": [],
            },
        },
        "rig": {
            "Configure_S_Parameter_Sweep": {
                "scpi": ":CALCulate:PARameter:DEFine '<param>';:SENSe:FREQuency:STARt <start>;:SENSe:FREQuency:STOP <stop>;:SENSe:SWEep:POINts <points>",
                "scpi_fast": ":CALC:PAR:DEF '<param>';:SENS:FREQ:STAR <start>;:SENS:FREQ:STOP <stop>;:SENS:SWE:POIN <points>",
                "description": "Configure S-parameter, sweep frequency bounds, and number of sweep points in one atomic operation",
                "subsystem": "CONFigure",
                "group": "Measurement Configuration",
                "args": ["param", "start", "stop", "points"],
                "arg": {
                    "kind": "multi",
                    "parameters": {
                        "param": {"kind": "enum", "values": ["S11", "S21", "S12", "S22"]},
                        "start": {"kind": "numeric", "unit": "Hz"},
                        "stop": {"kind": "numeric", "unit": "Hz"},
                        "points": {"kind": "numeric", "min": 2, "max": 100001},
                    },
                },
            },
        },
    },
}

# Primary donor models for families with authored .komand files
PRIMARY_DONOR_MODELS = {
    "DMM": "34401A",
    "Generator": "33220A",
    "Oscilloscope": "54641D",
    "Power": "66101A",
    "Load": "6060B",
    "Spectrum": "N9340B",
    "Router": "3235",
    "Distortion": "Porta_one",
    "LCR": "4263A",
}


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
        mqtt_info["reading_topic"] = f"APK.audio/Device/<device>/Reading/{cmd_name}"
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
        try:
            with open(gui_file, 'r', encoding='utf-8') as f:
                gui_data = json.load(f)
        except Exception:
            pass

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


def main():
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
        and d not in ('src', 'SRC')
    ))

    missing = [c for c in classes if c not in family_lanes]
    if missing:
        raise SystemExit(
            "manifest.json declares no tab for " + ", ".join(missing) +
            " — every class needs one before a port lane can be derived."
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
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump(api_doc, f, indent=2)
                f.write('\n')

            # 2. ONE NAME PER FILE. There used to be an `api.json` symlink beside
            #    every spec pointing at `<Model>.api.json`. It is swept away here
            #    rather than merely no longer written, because the generic name
            #    is the whole problem: `SMU/2410/api.json` and
            #    `DMM/34411A/api.json` are the same string, so an open file, a
            #    grep hit and a stack trace all stopped saying WHICH instrument
            #    they meant. `<Model>.api.json` never loses that. Nothing read
            #    the symlink — it was convenience, and it cost identity.
            stale = os.path.join(model_dir, "api.json")
            if os.path.islink(stale) or os.path.isfile(stale):
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
    with open(PORTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(ports_doc, f, indent=2)
        f.write('\n')

    print(f" Successfully generated API specifications for {generated} devices across {len(classes)} families.")
    print(f" Total commands presented: {total_commands}")
    if taken:
        print(f" Ports allocated: {len(taken)} in {min(taken)}-{max(taken)} -> _komand/ports.json")
    if swept:
        print(f" Swept {len(swept)} stale bare api.json file(s); the spec is <Model>.api.json only.")


if __name__ == '__main__':
    main()
