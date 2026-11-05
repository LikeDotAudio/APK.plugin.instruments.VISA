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



import compile_grab as cg  # noqa: E402

API = {'family': 'DMM', 'endpoints': {
    'get': {'Get_Func': {'scpi': ':FUNCtion?', 'scpi_fast': ':FUNC?', 'args': []},
            'Get_Range': {'scpi': ':VOLTage:RANGe?', 'scpi_fast': ':VOLT:RANG?', 'args': []},
            'Get_Screen': {'scpi': ':DISPlay:DATA?', 'args': [], 'returns': {'type': 'BLOCK'}},
            'Get_Chan': {'scpi': ':CHAN<n>:SCAL?', 'args': ['n']}},
    'nab': {'Get_Func': {'scpi': ':FUNCtion?', 'scpi_fast': ':FUNC?'},
            'Get_Range': {'scpi': ':VOLTage:RANGe?', 'scpi_fast': ':VOLT:RANG?'},
            'Settings': {'scpi': ':FUNC?;:VOLT:RANG?'}},
}}
EVIDENCE = {'family': 'DMM', 'units': ['visa/DMM/X/A', 'visa/DMM/X/B'],
            'qualified': [{'command': ':volt:rang?', 'units': ['visa/DMM/X/B'], 'first': 2.0},
                          {'command': ':FUNC?', 'units': ['visa/DMM/X/A'], 'first': 1.0},
                          {'command': ':DISPlay:DATA?', 'units': ['visa/DMM/X/A'], 'first': 3.0},
                          {'command': ':SYST:NOT:IN:TABLE?', 'units': ['visa/DMM/X/A'], 'first': 4.0}],
            'refused': [{'command': ':CAL:SEC?', 'why': 'refused: -113'}]}


class Grab(unittest.TestCase):
    """GRAB is compiled from single queries the bench answered alone (2026-11-04)."""

    def test_only_qualified_single_arg_free_library_queries_are_compiled(self):
        doc = cg.compile_model('X', EVIDENCE, API, now=0)
        self.assertEqual([c['endpoint'] for c in doc['commands']], ['Get_Func', 'Get_Range'],
                         'the library order; no block (screen), nothing outside the table')
        self.assertEqual(doc['commands'][1]['query'], ':volt:rang?', 'the query exactly as the unit answered it')
        self.assertEqual(doc['refused'], [{'query': ':CAL:SEC?', 'why': 'refused: -113'}])

    def test_no_evidence_no_file(self):
        self.assertIsNone(cg.compile_model('X', {'qualified': []}, API))

    def test_grab_is_one_compound_nab_of_exactly_the_qualified_queries(self):
        doc = cg.compile_model('X', EVIDENCE, API, now=0)
        eps = {'get': dict(API['endpoints']['get']), 'nab': dict(API['endpoints']['nab'])}
        out = g.grab_endpoints('DMM', doc, eps)
        self.assertEqual(set(out), {'GRAB'}, 'short enough: no parts')
        grab = out['GRAB']
        self.assertEqual(grab['verb'], 'nab')
        self.assertEqual(grab['scpi'], ':FUNC?;:volt:rang?')
        self.assertEqual(grab['returns'], {'count': 2, 'type': 'LIST'})
        self.assertEqual(grab['grab']['commands'], ['Get_Func', 'Get_Range'])
        self.assertEqual(grab['mqtt']['payload_format'], {'command': 'GRAB'})

    def test_an_arbitrary_ascii_answer_goes_last_ieee_488_2(self):
        doc = {'model': 'X', 'commands': [{'endpoint': 'E', 'query': '*ESE?'}, {'endpoint': 'I', 'query': '*IDN?'},
                                          {'endpoint': 'F', 'query': ':FUNC?'}]}
        out = g.grab_endpoints('DMM', doc, {'get': {'E': {}, 'I': {}, 'F': {}}, 'nab': {}})
        self.assertEqual(out['GRAB']['scpi'], '*ESE?;:FUNC?;*IDN?')
        self.assertEqual(out['GRAB']['grab']['commands'], ['E', 'F', 'I'], 'names stay matched to answers')

    def test_a_command_gone_from_the_tables_leaves_the_grab(self):
        doc = cg.compile_model('X', EVIDENCE, API, now=0)
        out = g.grab_endpoints('DMM', doc, {'get': {'Get_Func': {}}, 'nab': {}})
        self.assertEqual(out['GRAB']['grab']['commands'], ['Get_Func'])

    def test_a_long_grab_is_also_published_in_parts_within_the_buffer(self):
        queries = [f':SENS{i}:FUNC?' for i in range(60)]
        doc = {'model': 'X', 'commands': [{'endpoint': f'Q{i}', 'query': q} for i, q in enumerate(queries)]}
        eps = {'get': {f'Q{i}': {} for i in range(60)}, 'nab': {}}
        out = g.grab_endpoints('DMM', doc, eps)
        parts = [k for k in out if k != 'GRAB']
        self.assertGreater(len(parts), 1)
        self.assertEqual(out['GRAB']['grab']['chunks'], parts)
        self.assertTrue(all(len(out[p]['scpi'].encode()) <= g.GRAB_MAX_BYTES for p in parts))
        self.assertEqual(';'.join(out[p]['scpi'] for p in parts), out['GRAB']['scpi'], 'the same queries, the same order')

    def test_a_model_without_evidence_has_no_grab_in_the_shipped_tree(self):
        for family, folder in g.load_families().items():
            for model in sorted(os.listdir(os.path.join(g.INSTRUMENTS_ROOT, folder))):
                api_path = os.path.join(g.INSTRUMENTS_ROOT, folder, model, f'{model}.api.json')
                if not os.path.isfile(api_path):
                    continue
                has_grab = 'GRAB' in json.load(open(api_path)).get('endpoints', {}).get('nab', {})
                has_file = os.path.isfile(os.path.join(g.INSTRUMENTS_ROOT, folder, model, f'{model}.qualified.json'))
                self.assertEqual(has_grab, has_file, f'{family}/{model}: GRAB iff bench evidence')


if __name__ == '__main__':
    unittest.main()
