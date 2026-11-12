# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""A SET with options = the selector AND one SET per option (expand_selectors.py, 2026-11-11)."""
import unittest
from expand_selectors import expand, MARK


def table(**sets):
    return {"model": "M", "family": "F", "set": sets, "do": {}, "rig": {}, "nab": {}}


SEL = {"scpi": ":CALCulate1:FORMat <param>", "scpiFast": ":CALC1:FORM <param>",
       "description": "Selects it.", "args": ["param"], "subsystem": "CALCulate",
       "arg": {"kind": "enum", "values": ["CP", "MLIN", '"FIMP"'], "labels": {"CP": "parallel capacitance"}}}


class ExpandSelectors(unittest.TestCase):
    def test_selector_kept_and_one_set_per_option(self):
        out, clashes = expand(table(Primary_Parameter=SEL))
        s = out["set"]
        self.assertEqual(s["Primary_Parameter"], SEL)
        self.assertEqual(s["Primary_Parameter_CP"]["scpi"], ":CALCulate1:FORMat CP")
        self.assertEqual(s["Primary_Parameter_MLIN"]["scpiFast"], ":CALC1:FORM MLIN")
        self.assertEqual(s["Primary_Parameter_FIMP"]["scpi"], ':CALCulate1:FORMat "FIMP"')
        self.assertIn("parallel capacitance", s["Primary_Parameter_CP"]["description"])
        self.assertTrue(all(s[n]["unverified"] and "args" not in s[n] for n in s if n != "Primary_Parameter"))
        self.assertEqual(clashes, [])

    def test_rerun_changes_nothing_and_dropped_options_go(self):
        once, _ = expand(table(Primary_Parameter=SEL))
        twice, _ = expand(once)
        self.assertEqual(once, twice)
        fewer = dict(SEL, arg={"kind": "enum", "values": ["CP"]})
        once["set"]["Primary_Parameter"] = fewer
        out, _ = expand(once)
        self.assertEqual(sorted(out["set"]), ["Primary_Parameter", "Primary_Parameter_CP"])

    def test_hand_written_name_wins(self):
        mine = {"scpi": ":CALC1:FORM CP", "description": "by hand"}
        out, clashes = expand(table(Primary_Parameter=SEL, Primary_Parameter_CP=mine))
        self.assertEqual(out["set"]["Primary_Parameter_CP"], mine)
        self.assertEqual(clashes, ["Primary_Parameter_CP"])

    def test_no_options_or_no_placeholder_no_individuals(self):
        bare = {"scpi": ":TRIG:SOUR <source>", "description": "x", "args": ["source"], "arg": {"kind": "enum"}}
        two = {"scpi": ":A <a>,<b>", "description": "x", "arg": {"values": ["1"]}}
        out, _ = expand(table(T=bare, U=two))
        self.assertEqual(sorted(out["set"]), ["T", "U"])
        self.assertTrue(MARK)


if __name__ == "__main__":
    unittest.main()
