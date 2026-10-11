"""Behavior checks for preserved source functions, using only invented inputs."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "original"))
from population_metrics import calculate_population_metrics, impute_missing_data

GIS_IMPORT_ERROR = None
try:
    import geopandas as gpd
    from shapely.geometry import box

    from demographic_overlay import calculate_weighted_features
    from od_geometry import create_od_movement_gdf
except ImportError as error:
    GIS_IMPORT_ERROR = str(error)


FEATURES = [
    "avgHouseholdSize", "pctNonWhite(%)", "pctUnemployment(%)", "pctPoverty(%)",
    "pctDisability(%)", "pctElder(%)", "pctBachelorBelow(%)",
    "pctNoHealthInsurance(%)", "pctFemale(%)", "pctChildren(%)",
    "pctCarOwnership(%)", "pctHomeOwnership(%)", "totalPopulation",
    "medianHHIncome",
]


class OriginalPopulationTests(unittest.TestCase):
    def test_percentage_units_custom_columns_and_input_copy(self):
        source = pd.DataFrame({"baseline": [8, 8, 8], "crisis": [4, 12, 8]})
        original = source.copy(deep=True)
        result = calculate_population_metrics(source, "baseline", "crisis")
        np.testing.assert_allclose(result["evacuation_rate"], [50, 0, 0])
        np.testing.assert_allclose(result["influx_rate"], [0, 50, 0])
        np.testing.assert_allclose(result["percentage_change"], [-50, 50, 0])
        result.loc[0, "baseline"] = 999
        pd.testing.assert_frame_equal(source, original)

    def test_source_does_not_validate_zero_baseline(self):
        source = pd.DataFrame({"n_baseline": [0, 0], "n_crisis": [1, 0]})
        result = calculate_population_metrics(source)
        self.assertTrue(np.isposinf(result.loc[0, "influx_rate"]))
        self.assertTrue(np.isposinf(result.loc[0, "percentage_change"]))
        self.assertTrue(np.isnan(result.loc[1, "percentage_change"]))

    @staticmethod
    def incomplete_panel(indices, crisis):
        dates = pd.date_range("2000-01-01", periods=7)
        incomplete = pd.DataFrame({
            "quadkey": ["Invented A"] * len(indices),
            "ds": dates[indices],
            "n_baseline": np.asarray(crisis, dtype=float) * 10,
            "n_crisis": np.asarray(crisis, dtype=float),
        })
        complete = pd.DataFrame({
            "quadkey": ["Invented B"] * len(dates), "ds": dates,
            "n_baseline": [100.0] * len(dates), "n_crisis": [10.0] * len(dates),
        })
        return pd.concat([incomplete, complete], ignore_index=True)

    def test_first_three_positions_use_three_future_valid_values(self):
        source = self.incomplete_panel([3, 4, 5, 6], [30, 60, 90, 120])
        original = source.copy(deep=True)
        result = impute_missing_data(source)
        tile = result[result["quadkey"] == "Invented A"]
        np.testing.assert_allclose(tile["n_crisis"], [60, 60, 60, 30, 60, 90, 120])
        np.testing.assert_allclose(tile["n_baseline"], [600, 600, 600, 300, 600, 900, 1200])
        pd.testing.assert_frame_equal(source, original)

    def test_later_positions_use_preceding_three_including_earlier_fill(self):
        source = self.incomplete_panel([0, 1, 2, 3, 6], [10, 20, 30, 40, 70])
        result = impute_missing_data(source)
        tile = result[result["quadkey"] == "Invented A"]
        np.testing.assert_allclose(tile["n_crisis"], [10, 20, 30, 40, 30, 100 / 3, 70])
        np.testing.assert_allclose(tile["n_baseline"], [100, 200, 300, 400, 300, 1000 / 3, 700])

    def test_global_date_universe_and_complete_tiles_are_not_imputed(self):
        dates = pd.to_datetime(["2000-01-01", "2000-01-02", "2000-01-04"])
        source = pd.DataFrame({
            "quadkey": ["Invented A", "Invented A"] + ["Invented B"] * 3,
            "ds": [dates[0], dates[2]] + list(dates),
            "n_baseline": [100.0, 200.0, 100.0, np.nan, 100.0],
            "n_crisis": [10.0, 20.0, 10.0, np.nan, 10.0],
        })
        result = impute_missing_data(source)
        tile_a = result[result["quadkey"] == "Invented A"]
        self.assertEqual(set(tile_a["ds"]), set(dates))
        self.assertNotIn(pd.Timestamp("2000-01-03"), set(result["ds"]))
        # With only one future observation, the early-gap rule uses that value.
        self.assertEqual(tile_a.loc[tile_a["ds"] == dates[1], "n_crisis"].item(), 20)
        tile_b = result[result["quadkey"] == "Invented B"]
        # Original code only visits tiles that lack at least one global date.
        self.assertTrue(tile_b.loc[tile_b["ds"] == dates[1], "n_crisis"].isna().all())


@unittest.skipIf(GIS_IMPORT_ERROR is not None,
                 f"optional GeoPandas/Shapely spatial dependencies unavailable: {GIS_IMPORT_ERROR}")
class OriginalSpatialTests(unittest.TestCase):
    def test_od_grouping_sort_and_projected_endpoint_direction(self):
        source = pd.DataFrame({
            "start_quadkey": ["Invented A"] * 3,
            "end_quadkey": ["Invented B", "Invented B", "Invented C"],
            "n_baseline": [10, 20, 7], "n_crisis": [6, 9, 25],
            "start_latitude": [0.0] * 3, "start_longitude": [0.0] * 3,
            "end_latitude": [0.0, 0.0, 0.01],
            "end_longitude": [0.01, 0.01, 0.0],
        })
        original = source.copy(deep=True)
        result = create_od_movement_gdf(source)
        self.assertEqual(result.crs.to_epsg(), 3857)
        self.assertEqual(result["end_quadkey"].tolist(), ["Invented C", "Invented B"])
        self.assertEqual(result["n_baseline"].tolist(), [7, 30])
        self.assertEqual(result["n_crisis"].tolist(), [25, 15])
        endpoints = {row.end_quadkey: list(row.geometry.coords) for row in result.itertuples()}
        np.testing.assert_allclose(endpoints["Invented B"], [(0, 0), (1113.19490793, 0)], atol=1e-6)
        np.testing.assert_allclose(endpoints["Invented C"], [(0, 0), (0, 1113.19491358)], atol=1e-6)
        pd.testing.assert_frame_equal(source, original)

    @staticmethod
    def overlay_inputs():
        points = pd.DataFrame({
            "latitude": [0.0, 0.0], "longitude": [0.0, 0.0],
            "start_quadkey": ["Invented A", "Invented A"],
        })
        features = {feature: [1.0, 5.0] for feature in FEATURES}
        features.update({
            "totalPopulation": [100.0, 300.0],
            "medianHHIncome": ["250,000+", "50000"],
            "pctPoverty(%)": [np.nan, 40.0],
            "pctNoHealthInsurance(%)": [10.0, "unavailable"],
        })
        polygons = gpd.GeoDataFrame(features, geometry=[
            box(-100, -100, -50, 100), box(-50, -100, 100, 100),
        ], crs="EPSG:3857")
        return points, polygons

    def test_area_weighting_missing_feature_renormalization_and_prefix(self):
        points, polygons = self.overlay_inputs()
        original = polygons.copy(deep=True)
        # Source assigns to a dropna slice. Keep its definitions unchanged while
        # locally suppressing pandas' chained-assignment warning for this check.
        with pd.option_context("mode.chained_assignment", None):
            result = calculate_weighted_features(
                points, "latitude", "longitude", "start_quadkey", polygons, buffer_size=100)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.crs.to_epsg(), 3857)
        self.assertTrue(set(f"start_{feature}" for feature in FEATURES).issubset(result.columns))
        row = result.iloc[0]
        self.assertAlmostEqual(row["start_avgHouseholdSize"], 4)
        # totalPopulation is an area-weighted mean in the preserved source.
        self.assertAlmostEqual(row["start_totalPopulation"], 250)
        self.assertAlmostEqual(row["start_medianHHIncome"], 100000)
        self.assertAlmostEqual(row["start_pctPoverty(%)"], 40)
        self.assertAlmostEqual(row["start_pctNoHealthInsurance(%)"], 10)
        np.testing.assert_allclose(row.geometry.bounds, [-100, -100, 100, 100])
        pd.testing.assert_frame_equal(polygons, original)

    def test_default_buffer_size_is_square_half_width(self):
        points, polygons = self.overlay_inputs()
        with pd.option_context("mode.chained_assignment", None):
            result = calculate_weighted_features(
                points, "latitude", "longitude", "start_quadkey", polygons)
        np.testing.assert_allclose(result.geometry.iloc[0].bounds, [-1223, -1223, 1223, 1223])
        self.assertAlmostEqual(result.geometry.iloc[0].area, 2446 ** 2)


if __name__ == "__main__":
    unittest.main()
