"""Checks for aggregate metric interpretation, missing data, and OD direction."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
from evacuation_metrics_demo import (
    classify_evacuation_flows, damage_evacuation_disparity,
    population_metrics, run_demo,
)


class EvacuationTests(unittest.TestCase):
    def panel(self, crisis):
        return pd.DataFrame({"tile": ["A"] * len(crisis),
            "time": pd.date_range("2025-01-01", periods=len(crisis), freq="8h"),
            "baseline": [100] * len(crisis), "crisis": crisis})

    def test_population_influx_is_not_displacement(self):
        out = population_metrics(self.panel([120, 100, 40]))
        np.testing.assert_allclose(out["displacement_rate"], [0, 0, 0.6])
        np.testing.assert_allclose(out["population_deficit"], [0, 0, 60])
        np.testing.assert_allclose(out["cumulative_departure_pct"], [0, 0, 100])

    def test_no_departures_remains_undefined(self):
        out = population_metrics(self.panel([100, 120]))
        self.assertTrue(out["cumulative_departure_pct"].isna().all())

    def test_unsorted_time_and_tile_specific_cumulative_totals(self):
        a = self.panel([80, 40, 60])
        b = self.panel([90, 80, 100]); b["tile"] = "B"
        out = population_metrics(pd.concat([a, b]).sample(frac=1, random_state=2))
        np.testing.assert_allclose(out[out["tile"] == "A"]["cumulative_departure_pct"], [100/6, 200/3, 100])
        np.testing.assert_allclose(out[out["tile"] == "B"]["cumulative_departure_pct"], [100/3, 100, 100])

    def test_bad_inputs_are_not_silently_imputed(self):
        for crisis in [[100, np.nan], [100, -1]]:
            with self.assertRaises(ValueError): population_metrics(self.panel(crisis))
        duplicate = pd.concat([self.panel([100]), self.panel([100])])
        with self.assertRaises(ValueError): population_metrics(duplicate)
        zero_base = self.panel([50]); zero_base["baseline"] = 0
        with self.assertRaises(ValueError): population_metrics(zero_base)

    def test_dedi_one_sided_gap_and_complete_damage(self):
        self.assertEqual(damage_evacuation_disparity(0.3, 0.5), 0)
        self.assertAlmostEqual(damage_evacuation_disparity(0.8, 0.4), 2)
        with self.assertRaises(ValueError): damage_evacuation_disparity(1, 0.4)

    def test_direction_classification_and_zero_baseline(self):
        demo = run_demo()
        self.assertEqual([x["is_evacuation_flow"] for x in demo["evacuation_flow_selection"]], [True, True, False, False])
        flows = pd.DataFrame(demo["evacuation_flow_selection"])
        flows.loc[0, "baseline_count"] = 0
        out = classify_evacuation_flows(flows)
        self.assertTrue(np.isnan(out.loc[0, "change_from_baseline_pct"]))
        flows["origin_in_zone"] = flows["origin_in_zone"].astype(object)
        flows.loc[0, "origin_in_zone"] = "False"
        with self.assertRaises(ValueError): classify_evacuation_flows(flows)


if __name__ == "__main__":
    unittest.main()
