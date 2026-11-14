import unittest
import os
import sys

# Ensure backend importable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.data_loader import target_catalog, read_fits, compute_astrophysical_stretch

class TestDataLoader(unittest.TestCase):
    def test_target_discovery(self):
        targets = target_catalog.list_available_targets()
        self.assertGreaterEqual(len(targets), 1, "Should discover at least 1 archive target")
        target_keys = [t["key"] for t in targets]
        self.assertIn("barnards_star", target_keys, "Barnards Star must be discovered")

    def test_spectral_frames_loading_wide_and_core(self):
        # Wide mode (30 arcmin)
        wide_frames = target_catalog.get_target_frames("barnards_star", fov_mode="wide", blink_mode="spectral")
        self.assertGreaterEqual(len(wide_frames), 6, "Barnards Star should have at least 6 SPHEREx detector frames")
        
        d1 = wide_frames[0]
        self.assertEqual(d1["width"], 256)
        self.assertEqual(d1["height"], 256)
        self.assertEqual(len(d1["pixels"]), 256 * 256)
        self.assertTrue(d1["is_real_data"])
        self.assertGreater(d1["fov_arcmin"], 20.0, "Wide field should be ~30 arcminutes")

        # Core mode (6.5 arcmin stamp)
        core_frames = target_catalog.get_target_frames("barnards_star", fov_mode="core", blink_mode="spectral")
        self.assertEqual(len(core_frames), len(wide_frames))
        c1 = core_frames[0]
        self.assertEqual(c1["width"], 128)
        self.assertEqual(c1["height"], 128)
        self.assertEqual(len(c1["pixels"]), 128 * 128)
        self.assertLess(c1["fov_arcmin"], 15.0, "Core stamp should be ~13 arcminutes or less")

    def test_temporal_frames_loading(self):
        temp_frames = target_catalog.get_target_frames("barnards_star", fov_mode="wide", blink_mode="temporal")
        self.assertGreaterEqual(len(temp_frames), 2, "Barnards Star should have multi-epoch temporal frames")
        for f in temp_frames:
            self.assertTrue(f["is_real_data"])
            self.assertIn("WISE", f["instrument"])

    def test_pipeline_real_fits_orchestration(self):
        from backend.pipeline import execute_pipeline
        # Wide mode (30 arcmin)
        res_wide = execute_pipeline("Barnard's Star", fov_mode="wide", blink_mode="spectral")
        self.assertEqual(res_wide["status"], "success")
        self.assertTrue(res_wide["is_real_data"])
        self.assertEqual(res_wide["fov_mode"], "wide")
        self.assertGreaterEqual(len(res_wide["frames"]), 6)
        f0 = res_wide["frames"][0]
        self.assertTrue(f0["is_real_data"])
        self.assertIn("fits", f0["source_file"].lower())
        self.assertEqual(len(f0["rgb_pixels"]), 256)
        self.assertEqual(len(f0["rgb_pixels"][0]), 256)

        # Core mode (zoomed-in core stamp)
        res_core = execute_pipeline("Barnard's Star", fov_mode="core", blink_mode="spectral")
        self.assertEqual(res_core["status"], "success")
        self.assertTrue(res_core["is_real_data"])
        self.assertEqual(res_core["fov_mode"], "core")
        c0 = res_core["frames"][0]
        self.assertEqual(len(c0["rgb_pixels"]), 128)
        self.assertEqual(len(c0["rgb_pixels"][0]), 128)

        # Forced simulated mode
        res_sim = execute_pipeline("Barnard's Star", source_mode="simulated")
        self.assertEqual(res_sim["status"], "success")
        self.assertEqual(res_sim.get("is_real_data", False), False)
        self.assertEqual(len(res_sim["frames"]), 4)

if __name__ == "__main__":
    unittest.main()
