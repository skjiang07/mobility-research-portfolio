import json
from datetime import timedelta
from pathlib import Path
import sys
import unittest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
from activity_demo import synthetic_points, point_labels_to_segments, evaluate_segments_temporal_iou, build_messages


class ActivityChecks(unittest.TestCase):
    def test_duration_threshold_and_user_boundary(self):
        points = synthetic_points()
        duplicate = points.copy()
        duplicate["user_id"] = "invented-person-B"
        result = point_labels_to_segments(pd.concat([points, duplicate]))
        self.assertEqual(len(result), 4)
        self.assertEqual(set(result.duration_s), {300.0})
        self.assertTrue(point_labels_to_segments(points, min_duration_s=301).empty)

    def test_long_gap_splits_stay(self):
        points = synthetic_points().iloc[:6].copy()
        points.loc[points.index[3:], "tracked_at"] = pd.to_datetime([
            t.to_pydatetime() + timedelta(hours=2) for t in points.tracked_at.iloc[3:]
        ])
        self.assertTrue(point_labels_to_segments(points).empty)

    def test_duplicate_prediction_only_matches_once(self):
        segment = {"user_id": "A", "start_time": "2026-01-01 08:00",
                   "end_time": "2026-01-01 09:00"}
        metrics = evaluate_segments_temporal_iou(pd.DataFrame([segment, segment]), pd.DataFrame([segment]))
        self.assertEqual(metrics["n_match"], 1)
        self.assertEqual(metrics["segment_precision"], 0.5)
        self.assertEqual(metrics["segment_recall"], 1.0)

    def test_inference_payload_excludes_target(self):
        messages = build_messages(pd.Series({"purpose_category": "Home"}), include_label=False)
        self.assertEqual([x["role"] for x in messages], ["system", "user"])
        self.assertNotIn("purpose_category", json.loads(messages[1]["content"]))
        with self.assertRaises(ValueError):
            build_messages(pd.Series({"purpose_category": "invalid"}), include_label=True)

    def test_empty_evaluation_with_schema(self):
        empty = pd.DataFrame(columns=["user_id", "start_time", "end_time"])
        metrics = evaluate_segments_temporal_iou(empty, empty)
        self.assertEqual(metrics["n_match"], 0)
        self.assertEqual(metrics["segment_f1"], 0)


if __name__ == "__main__":
    unittest.main()
