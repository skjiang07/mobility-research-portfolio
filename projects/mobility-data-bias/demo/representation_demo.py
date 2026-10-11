"""Synthetic demonstration of between-area and within-area representation.

No observations from the study are used. Dense NumPy distances replace the
original scikit-learn neighbor search only to keep this small demo portable.
The representation equations match the selected original function extracts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "original"))
from sampling_representation import compute_rr, compute_sampling_ratio


def average_knn_distance(points: np.ndarray, k: int = 5) -> float:
    """Average distance to the k closest other points in planar coordinates."""
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError("points must be a finite N x 2 array")
    if not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    if len(points) <= k:
        return float("nan")
    distances = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
    np.fill_diagonal(distances, np.inf)
    return float(np.sort(distances, axis=1)[:, :k].mean())


def representation_score(observed_distance: float, reference_distance: float) -> float:
    """Original M = exp(-abs(r / h - 1)); a match has score 1."""
    if not np.isfinite([observed_distance, reference_distance]).all():
        raise ValueError("distances must be finite")
    if observed_distance < 0 or reference_distance <= 0:
        raise ValueError("observed distance must be nonnegative; reference must be positive")
    return float(np.exp(-abs(observed_distance / reference_distance - 1)))


def within_area_score(points: np.ndarray, *, seed: int = 20261010, n_sim: int = 50) -> float:
    """Compare synthetic points with uniform draws in a 1 km x 1 km square."""
    if not isinstance(n_sim, int) or n_sim < 1:
        raise ValueError("n_sim must be a positive integer")
    r = average_knn_distance(points)
    if not np.isfinite(r):
        raise ValueError("more than k points are required")
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n_sim):
        reference = rng.uniform(0, 1000, size=(len(points), 2))
        h = average_knn_distance(reference)
        scores.append(representation_score(r, h))
    return float(np.mean(scores))


def run_demo() -> dict:
    # Artificial districts and counts: these are invented, not deidentified data.
    areas = pd.DataFrame({
        "area": ["Synthetic A", "Synthetic B", "Synthetic C", "Synthetic D"],
        "population": [1000, 2000, 3000, 4000],
        "sample_count": [100, 200, 150, 550],
    })
    areas = compute_sampling_ratio(areas, "population", "sample_count", "sampling_rate")
    areas = compute_rr(areas, "sample_count", "population", "relative_representation")
    areas["signed_mismatch"] = areas["relative_representation"] - 1

    rng = np.random.default_rng(20261010)
    uniform = rng.uniform(0, 1000, size=(80, 2))
    clustered = np.clip(rng.normal(500, 60, size=(80, 2)), 0, 1000)
    return {
        "data_status": "entirely synthetic; demonstration only",
        "between_area_metrics": areas.round(6).to_dict(orient="records"),
        "within_area_metrics": {
            "uniform_example": round(within_area_score(uniform), 6),
            "clustered_example": round(within_area_score(clustered), 6),
            "sample_count_each": 80,
            "reference_draws": 50,
            "k": 5,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
