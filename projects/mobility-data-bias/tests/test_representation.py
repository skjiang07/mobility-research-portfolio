"""Checks of interpretation and edge cases for the portable demonstration."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
from representation_demo import (
    average_knn_distance, compute_rr, compute_sampling_ratio,
    representation_score, run_demo, within_area_score,
)


class RepresentationTests(unittest.TestCase):
    def test_proportional_sampling_and_scale_invariance(self):
        df = pd.DataFrame({"population": [1000, 2000, 3000], "sample": [10, 20, 30]})
        first = compute_rr(df, "sample", "population", "rr")
        df["sample"] *= 5
        second = compute_rr(df, "sample", "population", "rr")
        np.testing.assert_allclose(first["rr"], 1)
        np.testing.assert_allclose(first["rr"], second["rr"])

    def test_sampling_rate_missing_denominator(self):
        df = pd.DataFrame({"population": [100, 0, None], "sample": [10, 1, 1]})
        out = compute_sampling_ratio(df, "population", "sample", "sr")
        self.assertEqual(out.loc[0, "sr"], 0.1)
        self.assertTrue(out.loc[1:, "sr"].isna().all())

    def test_self_distances_are_excluded(self):
        points = np.array([[0, 0], [3, 0], [0, 4]], dtype=float)
        self.assertAlmostEqual(average_knn_distance(points, k=1), 10 / 3)
        self.assertTrue(np.isnan(average_knn_distance(points, k=3)))

    def test_score_and_invalid_reference(self):
        self.assertEqual(representation_score(10, 10), 1)
        self.assertLess(representation_score(5, 10), 1)
        with self.assertRaises(ValueError):
            representation_score(10, 0)
        with self.assertRaises(ValueError):
            within_area_score(np.ones((10, 2)), n_sim=0)

    def test_synthetic_cluster_is_less_representative_and_reproducible(self):
        a = run_demo()
        self.assertEqual(a, run_demo())
        m = a["within_area_metrics"]
        self.assertGreater(m["uniform_example"], m["clustered_example"])


if __name__ == "__main__":
    unittest.main()
