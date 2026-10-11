"""New synthetic example using original segment and context functions.

No model training, LLM request, personal trajectory or empirical result.
"""
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "original"))
from stay_segments import point_labels_to_segments, evaluate_segments_temporal_iou
from purpose_payload import build_messages


def synthetic_points():
    times = pd.date_range("2026-01-01 08:00", periods=13, freq="min")
    return pd.DataFrame({
        "user_id": "invented-person-A", "tracked_at": times,
        "latitude": 0.0, "longitude": 0.0,
        "pred_label": [1] * 6 + [0] + [1] * 6,
        "pred_stay_prob": [0.95] * 6 + [0.05] + [0.9] * 6,
    })


def run_demo():
    segments = point_labels_to_segments(synthetic_points())
    # Invented reference intervals; no observed labels are used.
    reference = pd.DataFrame([
        {"user_id": "invented-person-A", "start_time": "2026-01-01 08:00",
         "end_time": "2026-01-01 08:06"},
        {"user_id": "invented-person-A", "start_time": "2026-01-01 08:07",
         "end_time": "2026-01-01 08:12"},
    ])
    metrics = evaluate_segments_temporal_iou(segments, reference)
    context = pd.Series({
        "start_ts": pd.Timestamp("2026-01-01 08:00"),
        "end_ts": pd.Timestamp("2026-01-01 08:05"),
        "duration_min": 5.0, "duration_hr": 5 / 60,
        "n_points": 6, "day_name": "Thursday", "start_hour": 8,
        "end_hour": 8, "is_weekend": False,
        "nearest_poi_category": "education", "inside_building": True,
        "is_near_user_daytime_anchor": True,
    })
    messages = build_messages(context, include_label=False)
    return {
        "scope": "New synthetic example; no trained model or API call; not paper reproduction.",
        "segments": json.loads(segments.to_json(orient="records", date_format="iso")),
        "evaluation": {k: v for k, v in metrics.items() if k != "matches"},
        "inference_messages": messages,
        "purpose_prediction": None,
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, allow_nan=False))
