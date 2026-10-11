"""Synthetic implementation of selected equations from Jiang et al. (2026).

This example was written for the portfolio. It is not original research code
and does not reproduce the paper. All demonstration inputs are invented.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd


def population_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    """Apply paper Eqs. (1), (2), (4), and (5) to a prepared tile-time panel.

The cumulative metric sums population deficits; it is not a count of unique
people departing. Missing counts must be handled before using this function.
"""
    required = ["tile", "time", "baseline", "crisis"]
    if not set(required).issubset(panel.columns):
        raise ValueError(f"panel needs columns: {required}")
    out = panel[required].copy()
    if out.empty or out["tile"].isna().any():
        raise ValueError("panel must have rows and nonmissing tile identifiers")
    out["time"] = pd.to_datetime(out["time"], utc=True, errors="raise")
    if out["time"].isna().any() or out.duplicated(["tile", "time"]).any():
        raise ValueError("tile-time keys must be nonmissing and unique")
    for col in ["baseline", "crisis"]:
        out[col] = pd.to_numeric(out[col], errors="raise")
        if not np.isfinite(out[col].to_numpy(dtype=float)).all():
            raise ValueError("counts must be finite; handle missing values explicitly")
    if (out["baseline"] <= 0).any() or (out["crisis"] < 0).any():
        raise ValueError("baseline must be positive and crisis must be nonnegative")
    out = out.sort_values(["tile", "time"]).reset_index(drop=True)
    out["population_change"] = (out["crisis"] - out["baseline"]) / out["baseline"]
    out["displacement_rate"] = (-out["population_change"]).clip(lower=0)
    out["population_deficit"] = (out["baseline"] - out["crisis"]).clip(lower=0)
    group = out.groupby("tile")["population_deficit"]
    total = group.transform("sum")
    out["cumulative_departure_pct"] = 100 * group.cumsum() / total.where(total > 0)
    return out


def damage_evacuation_disparity(damage_rate: float, displacement_rate: float) -> float:
    """Paper Eq. (3): max(0, D - E) / (1 - D), with a positive denominator."""
    if not np.isfinite([damage_rate, displacement_rate]).all():
        raise ValueError("rates must be finite")
    if not 0 <= damage_rate < 1 or not 0 <= displacement_rate <= 1:
        raise ValueError("require 0 <= damage < 1 and 0 <= displacement <= 1")
    return max(0.0, damage_rate - displacement_rate) / (1.0 - damage_rate)


def classify_evacuation_flows(flows: pd.DataFrame) -> pd.DataFrame:
    """Select outbound-zone flows or inter-zone flows moving farther from fire.

Geometry-based zone membership and fire-perimeter distance are supplied as
prepared inputs. This demo does not compute zone intersections or routes.
"""
    required = [
        "origin", "destination", "origin_in_zone", "destination_in_zone",
        "origin_fire_distance_km", "destination_fire_distance_km",
        "baseline_count", "crisis_count",
    ]
    if not set(required).issubset(flows.columns):
        raise ValueError(f"flows needs columns: {required}")
    out = flows[required].copy()
    if out.empty or out[["origin", "destination"]].isna().any().any():
        raise ValueError("flows must have rows and nonmissing OD identifiers")
    for col in ["origin_in_zone", "destination_in_zone"]:
        if out[col].isna().any() or not out[col].map(lambda v: isinstance(v, (bool, np.bool_))).all():
            raise ValueError("zone membership must be explicitly boolean")
    for col in ["origin_fire_distance_km", "destination_fire_distance_km", "baseline_count", "crisis_count"]:
        out[col] = pd.to_numeric(out[col], errors="raise")
        if not np.isfinite(out[col].to_numpy(dtype=float)).all() or (out[col] < 0).any():
            raise ValueError("counts and fire distances must be finite and nonnegative")
    outward = ~out["destination_in_zone"]
    farther = out["destination_fire_distance_km"] > out["origin_fire_distance_km"]
    out["is_evacuation_flow"] = out["origin_in_zone"] & (outward | farther)
    out["change_from_baseline_pct"] = 100 * (out["crisis_count"] - out["baseline_count"]) / out["baseline_count"].where(out["baseline_count"] > 0)
    return out


def run_demo() -> dict:
    times = pd.date_range("2025-01-01T00:00:00Z", periods=4, freq="8h")
    panel = pd.DataFrame({
        "tile": ["Synthetic A"] * 4 + ["Synthetic B"] * 4,
        "time": list(times) * 2,
        "baseline": [100] * 8,
        "crisis": [100, 80, 40, 60, 100, 110, 100, 105],
    })
    metrics = population_metrics(panel)
    metrics["time"] = metrics["time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # A->Outside qualifies; A->B qualifies because B is farther from fire.
    flows = pd.DataFrame({
        "origin": ["A", "A", "B", "Outside"],
        "destination": ["Outside", "B", "A", "A"],
        "origin_in_zone": [True, True, True, False],
        "destination_in_zone": [False, True, True, True],
        "origin_fire_distance_km": [1.0, 1.0, 4.0, 10.0],
        "destination_fire_distance_km": [10.0, 4.0, 1.0, 1.0],
        "baseline_count": [10, 5, 5, 20],
        "crisis_count": [30, 15, 3, 15],
    })
    classified = classify_evacuation_flows(flows)
    return {
        "data_status": "entirely synthetic; demonstration only",
        "population_metrics": json.loads(metrics.round(6).to_json(orient="records")),
        "evacuation_flow_selection": classified.to_dict(orient="records"),
        "dedi_example": {
            "damage_rate": 0.8, "displacement_rate": 0.4,
            "dedi": round(damage_evacuation_disparity(0.8, 0.4), 6),
        },
        "interpretation": "Population deficits and aggregate OD signals are proxies, not individual evacuation observations.",
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, allow_nan=False))
