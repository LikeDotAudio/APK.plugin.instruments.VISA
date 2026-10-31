#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""Unit tests for the INSTRUMENTS checks: schemas, catalogue agreement, data files.

    python3 -m unittest discover -s _komand -p 'test_*.py'
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_device_apis as g  # noqa: E402
import schema_check as sc  # noqa: E402


class Schemas(unittest.TestCase):
    def test_the_shipped_tree_is_valid(self):
        n, problems = sc.check_tree()
        self.assertGreater(n, 300)
        self.assertEqual(problems, [])

    def test_a_gui_with_a_typo_or_a_missing_field_is_refused(self):
        schema = sc.load_schema('gui.schema.json')
        good = {"model": "X", "manufacturer": "Y", "type": "DMM", "notes": ""}
        self.assertEqual(sc.validate(good, schema, schema), [])
        self.assertTrue(sc.validate(dict(good, manufactuer="Y"), schema, schema))
        self.assertTrue(sc.validate({"model": "X"}, schema, schema))
        self.assertTrue(sc.validate(dict(good, channels="2"), schema, schema))

    def test_a_command_needs_scpi_and_a_description(self):
        schema = sc.load_schema('komand.schema.json')
        doc = {"model": "M", "family": "DMM", "set": {"A": {"scpi": "X"}}, "do": {}, "rig": {}, "nab": {}}
        self.assertIn("missing required `description`", " ".join(sc.validate(doc, schema, schema)))

    def test_an_unsupported_schema_keyword_is_refused(self):
        self.assertTrue(sc.validate(1, {"oneOf": []}, {}))


class Catalogue(unittest.TestCase):
    def test_disagreeing_fields_are_named(self):
        out = g.catalogue_disagreements("M", {"manufacturer": "A", "notes": "n"}, {"manufacturer": "B", "notes": "n"})
        self.assertEqual(len(out), 1)
        self.assertIn("M.manufacturer", out[0])


class DataNotCode(unittest.TestCase):
    def test_baselines_and_donors_load_from_their_files(self):
        self.assertEqual(sorted(g.BASELINE_COMMANDS), ["Counter", "DAQ", "SMU", "VNA"])
        self.assertNotIn("_note", g.BASELINE_COMMANDS["DAQ"])
        self.assertEqual(g.PRIMARY_DONOR_MODELS["DMM"], "34401A")

    def test_the_families_index_resolves_every_folder(self):
        with open(os.path.join(g.INSTRUMENTS_ROOT, 'families.json'), encoding='utf-8') as f:
            families = json.load(f)["families"]
        for family, folder in families.items():
            self.assertTrue(os.path.isdir(os.path.join(g.INSTRUMENTS_ROOT, folder)), folder)
            self.assertEqual(g.family_directory(family), os.path.join(g.INSTRUMENTS_ROOT, folder))


if __name__ == '__main__':
    unittest.main()
