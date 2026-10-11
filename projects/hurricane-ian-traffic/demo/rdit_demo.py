"""New synthetic illustration of the published baseline RDiT specification.

Invented segment-hour outcomes and weather; no empirical replication or causal claim.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "original"))
from pti_metric import add_pti_column

CUTOFF = pd.Timestamp("2022-09-27 07:00:00")


def traffic_metrics(speed_mph, speed_limit_mph=60.0, segment_length_miles=1.0):
    """New helper: exact travel-time quantile plus original speed-quantile PTI.

    Equal segment length per observation; speed limit is the free-flow proxy.
    Strictly positive finite speeds are required. No speed values are imputed.
    """
    speeds = np.asarray(speed_mph, dtype=float)
    if speeds.ndim != 1 or not len(speeds) or not np.isfinite(speeds).all() or (speeds <= 0).any():
        raise ValueError("Supply a nonempty vector of finite positive speeds.")
    if not np.isfinite(speed_limit_mph) or speed_limit_mph <= 0:
        raise ValueError("Free-flow proxy must be finite and positive.")
    if not np.isfinite(segment_length_miles) or segment_length_miles <= 0:
        raise ValueError("Segment length must be finite and positive.")
    travel_hours = segment_length_miles / speeds
    exact_pti = np.percentile(travel_hours, 95) / (segment_length_miles / speed_limit_mph)
    historical = add_pti_column(pd.DataFrame({"speed": [speeds.tolist()], "speed_limit": [speed_limit_mph]}))
    return {"sms_mph": float(len(speeds) * segment_length_miles / travel_hours.sum()),
            "pti_travel_time_quantile": float(exact_pti),
            "pti_original_speed_quantile": float(historical.pti.iloc[0])}


def prepare_model_data(data, bandwidth_hours=48):
    """New explicit adapter for the paper's cutoff, window and log outcomes."""
    columns = {"timestamp", "segment", "sms", "pti", "wind", "water", "humidity", "rain"}
    if not columns.issubset(data.columns):
        raise ValueError("Missing required segment-hour model columns.")
    if not np.isfinite(bandwidth_hours) or bandwidth_hours <= 0:
        raise ValueError("Bandwidth must be finite and positive.")
    result = data.copy()
    result["timestamp"] = pd.to_datetime(result.timestamp, errors="raise")
    if result.timestamp.isna().any() or result.segment.isna().any():
        raise ValueError("Timestamps and segment identifiers cannot be missing.")
    if result.duplicated(["segment", "timestamp"]).any():
        raise ValueError("Duplicate segment-hour observations.")
    numeric = result[["sms", "pti", "wind", "water", "humidity", "rain"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (result[["sms", "pti"]] <= 0).any().any():
        raise ValueError("Outcomes must be positive; outcomes and controls must be finite.")
    result["hours"] = (result.timestamp - CUTOFF).dt.total_seconds() / 3600
    result = result[result.hours.abs() <= bandwidth_hours].copy()
    result["post"] = (result.hours >= 0).astype(int)
    if result.post.nunique() != 2:
        raise ValueError("The analysis window must include observations on both sides.")
    result["hour_of_day"] = result.timestamp.dt.hour
    result["ln_sms"] = np.log(result.sms)
    result["ln_pti"] = np.log(result.pti)
    return result


def fit_rdit(data, outcome="ln_sms", bandwidth_hours=48):
    if outcome not in {"ln_sms", "ln_pti"}:
        raise ValueError("Choose ln_sms or ln_pti.")
    prepared = prepare_model_data(data, bandwidth_hours)
    formula = (f"{outcome} ~ post + hours + I(hours ** 2) + I(hours ** 3)"
               " + wind + water + humidity + rain + C(segment) + C(hour_of_day)")
    model = smf.ols(formula, data=prepared, missing="raise")
    if np.linalg.matrix_rank(model.exog) < model.exog.shape[1]:
        raise ValueError("The synthetic model design is rank deficient.")
    if len(prepared) <= model.exog.shape[1]:
        raise ValueError("Insufficient observations for residual degrees of freedom.")
    # HC1 is chosen for this example only; it does not address temporal dependence.
    return model.fit(cov_type="HC1")


def synthetic_panel(seed=2026, noise_sd=0.01):
    rng = np.random.default_rng(seed)
    records = []
    for segment in range(4):
        for hour in range(-48, 49):
            wind, water, humidity, rain = rng.normal(size=4)
            timestamp = datetime(2022, 9, 27, 7) + timedelta(hours=hour)
            trend = 0.001 * hour + 0.000002 * hour**2 - 0.0000001 * hour**3
            controls = 0.01 * wind + 0.015 * water - 0.005 * humidity - 0.02 * rain
            cycle = 0.03 * np.cos(timestamp.hour * 2 * np.pi / 24)
            ln_sms = np.log(45) - 0.15 * (hour >= 0) + trend + controls + cycle + 0.04 * segment
            ln_pti = np.log(1.3) + 0.12 * (hour >= 0) - trend - controls - cycle - 0.02 * segment
            records.append({"timestamp": timestamp, "segment": f"invented-segment-{segment}",
                            "sms": np.exp(ln_sms + rng.normal(0, noise_sd)),
                            "pti": np.exp(ln_pti + rng.normal(0, noise_sd)),
                            "wind": wind, "water": water, "humidity": humidity, "rain": rain})
    return pd.DataFrame(records)


def run_demo():
    data = synthetic_panel()
    estimates = {}
    for outcome in ["ln_sms", "ln_pti"]:
        fit = fit_rdit(data, outcome)
        beta = float(fit.params["post"])
        estimates[outcome] = {"observations": int(fit.nobs), "post_log_coefficient": beta,
                              "percent_change": float(100 * np.expm1(beta))}
    return {"scope": "New synthetic illustration; not empirical findings or publication reproduction.",
            "metrics": traffic_metrics([30, 45, 60]),
            "rdit": estimates,
            "inference_note": "Demo HC1 covariance does not correct serial correlation; estimates are illustrative."}


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, allow_nan=False))
