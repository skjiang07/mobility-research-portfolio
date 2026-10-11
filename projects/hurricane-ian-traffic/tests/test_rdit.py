from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
from rdit_demo import CUTOFF, traffic_metrics, prepare_model_data, synthetic_panel, fit_rdit


class TrafficChecks(unittest.TestCase):
    def test_harmonic_speed_and_quantile_difference(self):
        result = traffic_metrics([30, 60])
        self.assertAlmostEqual(result["sms_mph"], 40)
        self.assertAlmostEqual(result["pti_travel_time_quantile"], 1.95)
        self.assertNotAlmostEqual(result["pti_travel_time_quantile"], result["pti_original_speed_quantile"])
        with self.assertRaises(ValueError):
            traffic_metrics([0, 60])

    def test_cutoff_and_window(self):
        prepared = prepare_model_data(synthetic_panel(), 24)
        self.assertEqual(len(prepared), 4 * 49)
        self.assertTrue((prepared.loc[prepared.timestamp == CUTOFF, "post"] == 1).all())
        self.assertTrue((prepared.loc[prepared.hours < 0, "post"] == 0).all())

    def test_recovers_known_synthetic_discontinuity(self):
        data = synthetic_panel(noise_sd=0)
        self.assertAlmostEqual(fit_rdit(data, "ln_sms").params["post"], -0.15, places=8)
        self.assertAlmostEqual(fit_rdit(data, "ln_pti").params["post"], 0.12, places=8)

    def test_invalid_outcomes_and_duplicates_rejected(self):
        data = synthetic_panel()
        with self.assertRaises(ValueError):
            prepare_model_data(pd.concat([data, data.iloc[:1]]))
        data.loc[0, "pti"] = np.nan
        with self.assertRaises(ValueError):
            prepare_model_data(data)


if __name__ == "__main__":
    unittest.main()
