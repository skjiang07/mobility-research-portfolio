"""Analytical checks for the synthetic illustration; no research data required."""

from dataclasses import replace
from datetime import datetime, timedelta
import unittest

from synthetic_demo import (
    Segment, Observation, synthetic_trip, estimate_trip,
    extract_segment_trips, aggregate_space_mean_speed, run_demo,
)


class MethodChecks(unittest.TestCase):
    def setUp(self):
        self.segment = Segment()
        self.start = datetime(2023, 10, 9, 7)

    def test_dwell_correction_and_three_components(self):
        estimate = estimate_trip(synthetic_trip("A", self.start, 10, 45), self.segment)
        self.assertTrue(estimate.dwelled)
        self.assertAlmostEqual(estimate.type1_s, 90)
        self.assertAlmostEqual(estimate.type2_s, 6)
        self.assertAlmostEqual(estimate.type3_s, 4)
        self.assertAlmostEqual(estimate.corrected_time_s, 100)
        self.assertAlmostEqual(estimate.observed_segment_time_s, 145)

    def test_exact_threshold_and_skipped_stop(self):
        below = estimate_trip(synthetic_trip("A", self.start, 10, 14), self.segment)
        exact = estimate_trip(synthetic_trip("A", self.start, 10, 15), self.segment)
        self.assertFalse(below.dwelled)
        self.assertAlmostEqual(below.corrected_time_s, 114)
        self.assertTrue(exact.dwelled)
        self.assertAlmostEqual(exact.corrected_time_s, 100)

    def test_distance_over_total_time_is_harmonic_not_arithmetic(self):
        estimates = [
            estimate_trip(synthetic_trip("A", self.start, 10, 45), self.segment),
            estimate_trip(synthetic_trip("B", self.start + timedelta(minutes=5), 5, 0), self.segment),
        ]
        output = aggregate_space_mean_speed(estimates, self.segment)[0]
        self.assertEqual(output["trip_count"], 2)
        self.assertAlmostEqual(output["total_corrected_time_s"], 300)
        self.assertAlmostEqual(output["space_mean_speed_mps"], 20 / 3, places=5)
        self.assertNotAlmostEqual(output["space_mean_speed_mps"], (10 + 5) / 2)

    def test_trip_id_date_identity_and_off_route_filter(self):
        points = synthetic_trip("same-id", self.start, 10, 0)
        points += synthetic_trip("same-id", self.start + timedelta(days=1), 10, 0)
        points += [Observation("outside", self.start, 500, 100, 10)]
        groups = extract_segment_trips(points, self.segment)
        self.assertEqual(set(groups), {("same-id", "2023-10-09"), ("same-id", "2023-10-10")})

    def test_interval_assignment_and_empty_intervals(self):
        estimate = estimate_trip(synthetic_trip("A", self.start + timedelta(minutes=16), 10, 0), self.segment)
        rows = aggregate_space_mean_speed([estimate], self.segment)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["interval_start"], "2023-10-09T07:15:00")
        self.assertEqual(aggregate_space_mean_speed([], self.segment), [])

    def test_invalid_boundary_and_zero_imputation_speed_fail_explicitly(self):
        points = synthetic_trip("A", self.start, 10, 0)
        with self.assertRaisesRegex(ValueError, "before and after"):
            estimate_trip(points[1:], self.segment)
        modified = [replace(p, speed_mps=0) if p.x_m in (470, 530) else p for p in points]
        with self.assertRaisesRegex(ValueError, "mean speed"):
            estimate_trip(modified, self.segment)

    def test_demo_uses_synthetic_results(self):
        output = run_demo()
        self.assertEqual(output["retained_trips"], 2)
        self.assertAlmostEqual(output["intervals"][0]["space_mean_speed_kph"], 24)


if __name__ == "__main__":
    unittest.main()
