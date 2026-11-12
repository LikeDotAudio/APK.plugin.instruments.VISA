#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""Unit tests for scpi_paths.py — every header a path in its model's own tree.

    python3 -m unittest -q test_scpi_paths      # from _komand/
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scpi_paths as sp  # noqa: E402

TREE = {'model': 'X', 'manual': 'test', 'roots': ['SYSTem', 'DATA', 'AM', 'FUNCtion', 'FREQuency', 'SENSe', 'VOLTage'],
        'optional': ['SENSe'], 'unresolved': {}}


def table(**verbs):
    t = {'model': 'X', 'family': 'T', 'set': {}, 'do': {}, 'rig': {}, 'nab': {}}
    for verb, cmds in verbs.items():
        t[verb] = {name: {'scpi': scpi, 'description': name} for name, scpi in cmds.items()}
    return t


def kinds(findings, notes=False):
    return sorted((f['kind'], f['where']) for f in findings if notes or f['kind'] not in sp.NOTES)


class Orphans(unittest.TestCase):
    def test_a_cut_off_parent_is_named_with_the_command_it_is_the_tail_of(self):
        t = table(nab={'Get_System_Beeper_State': 'SYSTem:BEEPer:STATe?', 'Get_Beeper_State': ':BEEPer:STATe?'})
        f = [x for x in sp.check_model(t, TREE) if x['kind'] == 'root']
        self.assertEqual([x['where'] for x in f], ['nab/Get_Beeper_State'])
        self.assertIn('SYSTem:BEEPer:STATe', f[0]['message'])
        self.assertIn('TRUNCATED', f[0]['message'])

    def test_the_colon_is_not_the_fault_the_missing_parent_is(self):
        t = table(nab={'Get_Square': 'FUNCtion:SQUare:DCYCle?', 'Orphan': 'SQUare:DCYCle?', 'Rooted': ':FUNCtion:SQUare:DCYCle?'})
        self.assertEqual(kinds(sp.check_model(t, TREE)), [('root', 'nab/Orphan')])

    def test_short_and_long_forms_and_a_default_node_are_the_same_path(self):
        t = table(set={'A': 'SENS:VOLT:RANG <r>', 'B': 'VOLTage:RANGe <r>', 'C': 'syst:beep:stat <s>'})
        self.assertEqual(kinds(sp.check_model(t, TREE)), [])

    def test_an_index_or_placeholder_still_resolves(self):
        t = table(set={'A': ':DECoder<n>:SPI:CLK <v>'})
        tree = dict(TREE, roots=TREE['roots'] + ['DECoder'])
        self.assertEqual(kinds(sp.check_model(t, tree)), [])


class Stacks(unittest.TestCase):
    def test_a_statement_after_a_semicolon_needs_the_root_colon_under_a_parent(self):
        t = table(rig={'Setup_AM': 'AM:INTernal:FUNCtion <s>;AM:INTernal:FREQuency <f>;AM:DEPTh <d>'})
        f = sp.check_model(t, TREE)
        self.assertEqual([x['kind'] for x in f], ['relative', 'relative'])
        self.assertIn('AM:INT:AM:INT:FREQ', f[0]['message'])

    def test_the_fixed_stack_and_a_legal_relative_one_pass(self):
        t = table(rig={'Fixed': 'AM:INTernal:FUNCtion <s>;:AM:INTernal:FREQuency <f>;:AM:DEPTh <d>',
                       'Relative': 'AM:INTernal:FUNCtion <s>;FREQuency <f>',
                       'Root': 'FUNCtion?;FREQuency?'},
                  nab={'F': 'AM:INTernal:FREQuency?'})
        self.assertEqual(kinds(sp.check_model(t, TREE)), [])

    def test_one_bad_member_of_a_stacked_nab_is_found(self):
        t = table(nab={'Stack': ':FUNCtion?;:FREQuency?;:ATTRibute:POINts?', 'Full': 'DATA:ATTRibute:POINts?'})
        self.assertEqual(kinds(sp.check_model(t, TREE)), [('root', 'nab/Stack')])


class Spelling(unittest.TestCase):
    def test_one_keyword_two_short_forms(self):
        t = table(nab={'A': 'SYSTem:MARKer?', 'B': 'SYSTem:MARker?'})
        self.assertIn(('spelling', ''), kinds(sp.check_model(t, TREE)))

    def test_a_spelling_the_manual_itself_writes_is_accepted(self):
        t = table(nab={'A': 'SYSTem:MARKer?', 'B': 'SYSTem:MARker?'})
        self.assertEqual(kinds(sp.check_model(t, dict(TREE, spellings={'MARKER': 'both in the guide'}))), [])


class Bookkeeping(unittest.TestCase):
    def test_unresolved_silences_only_while_it_is_still_true(self):
        t = table(do={'Odd': 'BACK:GOTO'})
        self.assertEqual(kinds(sp.check_model(t, dict(TREE, unresolved={'do/Odd': 'why'}))), [])
        fixed = table(do={'Odd': 'SYSTem:BEEPer'})
        self.assertEqual(kinds(sp.check_model(fixed, dict(TREE, unresolved={'do/Odd': 'why'}))), [('stale', 'do/Odd')])

    def test_a_retired_entry_is_never_judged(self):
        t = table(do={'Gone': 'BACK:GOTO'})
        t['do']['Gone'].update(retired=True, retired_because='x')
        self.assertEqual(kinds(sp.check_model(t, TREE)), [])

    def test_no_tree_is_a_finding(self):
        self.assertEqual(kinds(sp.check_model(table(), None)), [('tree', '')])

    def test_duplicates_are_notes_and_alias_of_settles_them(self):
        t = table(nab={'A': 'SYSTem:BEEPer:STATe?', 'B': ':SYST:BEEP:STAT?'})
        self.assertEqual(kinds(sp.check_model(t, TREE), notes=True), [('duplicate', 'nab/B')])
        t['nab']['B']['alias_of'] = 'A'
        self.assertEqual(kinds(sp.check_model(t, TREE), notes=True), [])

    def test_a_query_whose_format_disagrees_with_its_own_set_is_a_note(self):
        t = table(set={'Hold': 'FUNCtion:PULSe:HOLD <h>'}, nab={'Get_Hold': 'FUNCtion:PULSe:HOLD?'})
        t['set']['Hold']['arg'] = {'kind': 'enum', 'values': ['WIDT', 'DCYC']}
        t['nab']['Get_Hold']['returns'] = {'count': 1, 'type': 'NR3'}
        self.assertEqual(kinds(sp.check_model(t, TREE), notes=True), [('returns', 'nab/Get_Hold')])
        t['nab']['Get_Hold']['returns']['type'] = 'CRD'
        self.assertEqual(kinds(sp.check_model(t, TREE), notes=True), [])

    def test_the_shipped_tree_has_no_finding(self):
        n, findings = sp.check_tree()
        self.assertGreater(n, 0)
        self.assertEqual([f for f in findings if f['kind'] not in sp.NOTES], [])


if __name__ == '__main__':
    unittest.main()
