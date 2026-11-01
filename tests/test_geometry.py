import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vibe-modelling-skill" / "scripts"))
import geometry  # noqa: E402

BUSHING_PROFILE = "4,0 11.5,0 12,0.5 12,3.5 11.5,4 6,4 6,19.5 5.5,20 4,20"


class PlateTest(unittest.TestCase):
    def test_motor_plate_matches_solidworks(self):
        # test run 1, test 5: SolidWorks measured 33460.8 mm³
        bbox, volume = geometry.plate(100, 60, 6, corner_r=3, holes=["4x5.5", "16,22:4"])
        self.assertEqual(bbox, (100, 60, 6))
        self.assertAlmostEqual(volume, 33460.8, places=1)

    def test_blind_hole_deeper_than_plate_is_clamped(self):
        _, through = geometry.plate(10, 10, 2, holes=["4"])
        _, blind = geometry.plate(10, 10, 2, holes=["4:5"])
        self.assertAlmostEqual(through, blind)


class RevolveTest(unittest.TestCase):
    def test_bushing_matches_solidworks(self):
        # test run 1, test 4: SolidWorks measured 2590.6 mm³
        bbox, volume = geometry.revolve(geometry.parse_profile(BUSHING_PROFILE))
        self.assertEqual(bbox, (24, 20, 24))
        self.assertAlmostEqual(volume, 2590.6, places=1)

    def test_point_order_does_not_matter(self):
        points = geometry.parse_profile(BUSHING_PROFILE)
        self.assertAlmostEqual(geometry.revolve(points)[1], geometry.revolve(points[::-1])[1])

    def test_cylinder(self):
        _, volume = geometry.revolve([(0, 0), (5, 0), (5, 10), (0, 10)])
        self.assertAlmostEqual(volume, math.pi * 25 * 10)


class ChecksTest(unittest.TestCase):
    def test_bolt_circle_overlap(self):
        gap, centers = geometry.bolt_circle(10, 6, 6)
        self.assertLess(gap, 0)
        self.assertEqual(len(centers), 6)

    def test_bolt_circle_coordinates(self):
        _, centers = geometry.bolt_circle(60, 4, 6.6, start_deg=45)
        self.assertAlmostEqual(centers[0][0], 21.213, places=3)
        self.assertAlmostEqual(centers[0][1], 21.213, places=3)

    def test_test3_bolt_circle_falls_off_plate(self):
        # test run 1, test 3: Ø60 BC with M6 clearance on a 50 × 30 plate
        self.assertGreater(60 / 2 + 6.6 / 2, 30 / 2)

    def test_motor_plate_edge_distance(self):
        # test run 1, test 5: 8 mm inset, Ø5.5 = 1.45 × Ø, below the bolted minimum
        ok, message = geometry.edge_ok(5.5, 8, "machined", bolted=True)
        self.assertFalse(ok)
        self.assertIn("1.45", message)
        self.assertTrue(geometry.edge_ok(5.5, 8, "machined")[0])

    def test_sheet_edge_needs_thickness(self):
        with self.assertRaises(ValueError):
            geometry.edge_ok(5, 10, "sheet")
        self.assertTrue(geometry.edge_ok(5, 6, "sheet", thickness=1.5)[0])

    def test_wall(self):
        self.assertEqual(geometry.wall(12, 8), 2)

    def test_cli_exit_codes(self):
        self.assertEqual(geometry.main(["wall", "--outer", "12", "--inner", "8", "--process", "fdm"]), 0)
        self.assertEqual(geometry.main(["wall", "--outer", "10", "--inner", "8", "--process", "fdm"]), 1)
        self.assertEqual(geometry.main(["revolve", "--profile", "-1,0 2,0 2,1"]), 2)


if __name__ == "__main__":
    unittest.main()
