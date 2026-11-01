import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "vibe-modelling-skill" / "scripts"))
import lint_spec  # noqa: E402

PLATE = (ROOT / "examples" / "motor-plate-v1.txt").read_text(encoding="utf-8")


class ExamplesTest(unittest.TestCase):
    def test_examples_are_clean(self):
        for path in sorted((ROOT / "examples").glob("*.txt")):
            with self.subTest(path.name):
                self.assertEqual(lint_spec.lint(path.read_text(encoding="utf-8")), ([], []))


class BrokenSpecTest(unittest.TestCase):
    def assert_error(self, text, fragment):
        errors, _ = lint_spec.lint(text)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_missing_header(self):
        self.assert_error(PLATE.replace("ORIENTATION:", "NOTE:"), "missing ORIENTATION")

    def test_missing_version(self):
        self.assert_error(PLATE.replace("motor-plate v1", "motor-plate"), "no version")

    def test_missing_end_condition(self):
        self.assert_error(PLATE.replace("blind T, upward", "upward"), "no end condition")

    def test_single_slot_feature(self):
        self.assert_error(PLATE.replace("5. Corners: fillet R r · 4 vertical edges of Base", "5. Corners: fillet R r"), "fewer than 2 slots")

    def test_numbering(self):
        self.assert_error(PLATE.replace("5. Corners", "6. Corners"), "not numbered")

    def test_index_and_localized_references(self):
        self.assert_error(PLATE.replace("on top face of Base", "on Face2"), "index-based")
        self.assert_error(PLATE.replace("sketch on top plane", "sketch on Planta"), "localized plane")
        self.assert_error(PLATE.replace("4 vertical edges of Base", "4 vertical edges of Cut-Extrude1"), "CAD-generated")

    def test_undefined_and_unused_parameters(self):
        self.assert_error(PLATE.replace("hx=L/2−inset", "hx=L/2−margin"), "undefined margin")
        _, warnings = lint_spec.lint(PLATE.replace("r=3", "r=3  spare=1"))
        self.assertEqual(warnings, ["parameter spare is defined but never used"])

    def test_delta_needs_its_headers(self):
        self.assert_error("DELTA: motor-plate v1 → v2\nCHANGED: T 6 → 8\nEXPECT: bbox 100 × 60 × 8", "missing AFFECTED")


if __name__ == "__main__":
    unittest.main()
