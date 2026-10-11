"""Run preserved wildfire functions on invented inputs; no external data I/O.

This illustrates selected source behavior, not the empirical study. Spatial
examples use artificial coordinates near (0, 0) and require GeoPandas/Shapely.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "original"))
from population_metrics import calculate_population_metrics, impute_missing_data


def run_demo():
    dates = pd.date_range("2000-01-01", periods=4)
    panel = pd.DataFrame({
        "quadkey": ["Invented A"] * 3 + ["Invented B"] * 4,
        "ds": [dates[0], dates[2], dates[3]] + list(dates),
        "n_baseline": [100.0] * 7,
        "n_crisis": [100.0, 40.0, 60.0, 100.0, 110.0, 100.0, 120.0],
    })
    imputed = impute_missing_data(panel)
    metrics = calculate_population_metrics(imputed)
    metrics["ds"] = metrics["ds"].dt.strftime("%Y-%m-%d")
    result = {
        "data_status": "invented inputs; original functions; demonstration only",
        "population_functions": ["impute_missing_data", "calculate_population_metrics"],
        "population": json.loads(metrics.round(6).to_json(orient="records")),
        "source_assumptions": {
            "rate_units": "percent (50 means 50%)",
            "imputation_dates": "only dates present somewhere in the input panel",
            "baseline": "positive invented values; source divides without validation",
        },
    }
    try:
        import geopandas as gpd
        from shapely.geometry import box

        from demographic_overlay import calculate_weighted_features
        from od_geometry import create_od_movement_gdf
    except ImportError as error:
        result["spatial_status"] = f"skipped: optional GeoPandas/Shapely dependency unavailable ({error})"
        return result

    movements = pd.DataFrame({
        "start_quadkey": ["Invented A"] * 3,
        "end_quadkey": ["Invented B", "Invented B", "Invented C"],
        "n_baseline": [10, 20, 7], "n_crisis": [6, 9, 25],
        "start_latitude": [0.0] * 3, "start_longitude": [0.0] * 3,
        "end_latitude": [0.0, 0.0, 0.01], "end_longitude": [0.01, 0.01, 0.0],
    })
    od = create_od_movement_gdf(movements)
    result["od_function"] = "create_od_movement_gdf"
    result["od_projected_crs"] = str(od.crs)
    result["od"] = [{
        "origin": row.start_quadkey, "destination": row.end_quadkey,
        "baseline": int(row.n_baseline), "crisis": int(row.n_crisis),
        "projected_endpoints_m": [[round(x, 3), round(y, 3)] for x, y in row.geometry.coords],
    } for row in od.itertuples()]

    features = [
        "avgHouseholdSize", "pctNonWhite(%)", "pctUnemployment(%)", "pctPoverty(%)",
        "pctDisability(%)", "pctElder(%)", "pctBachelorBelow(%)",
        "pctNoHealthInsurance(%)", "pctFemale(%)", "pctChildren(%)",
        "pctCarOwnership(%)", "pctHomeOwnership(%)", "totalPopulation",
        "medianHHIncome",
    ]
    demographic_values = {feature: [1.0, 5.0] for feature in features}
    demographic_values.update({
        "totalPopulation": [100.0, 300.0], "medianHHIncome": ["250,000+", "50000"],
        "pctPoverty(%)": [None, 40.0],
    })
    # These invented polygons are already in the CRS expected by the source.
    demographics = gpd.GeoDataFrame(demographic_values, geometry=[
        box(-1223, -1223, -611.5, 1223), box(-611.5, -1223, 1223, 1223),
    ], crs="EPSG:3857")
    points = pd.DataFrame({
        "latitude": [0.0], "longitude": [0.0], "start_quadkey": ["Invented A"],
    })
    # Source assigns to a dropna slice; this local setting suppresses its pandas
    # warning without altering the preserved function or global pandas options.
    with pd.option_context("mode.chained_assignment", None):
        overlay = calculate_weighted_features(
            points, "latitude", "longitude", "start_quadkey", demographics)
    row = overlay.iloc[0]
    result["demographic_function"] = "calculate_weighted_features"
    result["demographic_overlay"] = {
        "polygon_crs": str(overlay.crs), "square_half_width_m": 1223,
        "square_full_width_m": 2446, "area_weighted_avgHouseholdSize": row["start_avgHouseholdSize"],
        "area_weighted_totalPopulation": row["start_totalPopulation"],
        "area_weighted_medianHHIncome": row["start_medianHHIncome"],
        "pctPoverty_after_missing_value_renormalization": row["start_pctPoverty(%)"],
    }
    return result


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, allow_nan=False))
