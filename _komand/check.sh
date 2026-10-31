#!/usr/bin/env bash
# INSTRUMENTS — THE local check (audit 2026-10-30 #1). No workflow (the root's
# rule: checks run by hand / .apk.scripts/check.sh before push); this is the one
# command, from anywhere:
#   PODS/POD.THICK/INSTRUMENTS/_komand/check.sh
# 1. generate_device_apis.py --check  specs + ports current, families.json and
#    manifest agree with the folders, .gui = knownDevices.json, every file valid
#    against _komand/schemas/, a broken .gui fails loudly
# 2. sort_komands.py --check          every .komand table in display order
# 3. unit tests                       schemas, catalogue rule, data files
# 4. cargo test                       the apkaudio-known-devices crate
set -euo pipefail
cd "$(dirname "$0")"
python3 generate_device_apis.py --check
python3 sort_komands.py --check
python3 -m unittest -q test_instruments
cargo test --offline -q
echo "✅ INSTRUMENTS check passed"
