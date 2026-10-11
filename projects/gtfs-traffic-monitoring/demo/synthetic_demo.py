"""Illustrate the published GTFS travel-time equations with invented trajectories.

This new, dependency-free demonstration is not an original research notebook
and does not reproduce the study's Gainesville data or reported results.
Coordinates are map-matched metres along a straight synthetic corridor; speed
is metres per second. See README.md for the GIS and validation scope.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import hypot, isfinite
import argparse
import json


@dataclass(frozen=True)
class Observation:
    trip_id: str
    timestamp: datetime
    x_m: float
    y_m: float
    speed_mps: float


@dataclass(frozen=True)
class Segment:
    segment_id: str = "synthetic-corridor"
    start_m: float = 0.0
    end_m: float = 1000.0
    route_buffer_m: float = 30.0
    stop_center_m: float = 500.0
    stop_radius_m: float = 20.0
    dwell_threshold_s: float = 15.0

    @property
    def length_m(self) -> float:
        return self.end_m - self.start_m


@dataclass(frozen=True)
class TripEstimate:
    trip_id: str
    service_date: str
    segment_id: str
    first_timestamp: datetime
    type1_s: float
    type2_s: float
    type3_s: float
    actual_stop_crossing_s: float
    imputed_stop_crossing_s: float
    dwelled: bool
    observed_segment_time_s: float

    @property
    def corrected_time_s(self) -> float:
        return self.type1_s + self.type2_s + self.type3_s


def segment_distance_m(point: Observation, segment: Segment) -> float:
    """Point-to-finite-line distance for the synthetic straight corridor."""
    nearest_x = min(max(point.x_m, segment.start_m), segment.end_m)
    return hypot(point.x_m - nearest_x, point.y_m)


def extract_segment_trips(
    observations: list[Observation], segment: Segment
) -> dict[tuple[str, str], list[Observation]]:
    """Algorithm 1: retain trips intersecting the buffer, keyed by ID and date.

    Adjacent observations from those trips are retained as boundary context for
    Equation 3. They are not counted as observations inside the road segment.
    """
    groups: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    selected: set[tuple[str, str]] = set()
    for point in observations:
        if not all(isfinite(v) for v in (point.x_m, point.y_m, point.speed_mps)):
            raise ValueError("Positions and speed must be finite.")
        if point.speed_mps < 0:
            raise ValueError("Speed cannot be negative.")
        key = (point.trip_id, point.timestamp.date().isoformat())
        groups[key].append(point)
        if segment_distance_m(point, segment) < segment.route_buffer_m:
            selected.add(key)
    return {
        key: sorted(groups[key], key=lambda point: point.timestamp)
        for key in sorted(selected)
    }


def seconds_between(first: Observation, last: Observation) -> float:
    seconds = (last.timestamp - first.timestamp).total_seconds()
    if seconds <= 0:
        raise ValueError("Observation timestamps must strictly increase.")
    return seconds


def estimate_trip(points: list[Observation], segment: Segment) -> TripEstimate:
    """Equations 1–4 for one forward trip with one interior stop buffer.

    The published method supports multiple stops/segments. This demonstration
    explicitly restricts geometry to one segment and one interior stop, while
    preserving all three travel-time components and the dwell decision rule.
    """
    if len(points) < 4:
        raise ValueError("A trip needs interior and adjacent boundary observations.")
    if segment.length_m <= 0 or segment.stop_radius_m <= 0:
        raise ValueError("Segment length and stop radius must be positive.")
    if segment.route_buffer_m <= 0 or segment.dwell_threshold_s < 0:
        raise ValueError("Route buffer must be positive and dwell threshold nonnegative.")
    if not segment.start_m < segment.stop_center_m - segment.stop_radius_m:
        raise ValueError("The stop buffer must be strictly inside the segment.")
    if not segment.stop_center_m + segment.stop_radius_m < segment.end_m:
        raise ValueError("The stop buffer must be strictly inside the segment.")
    if len({(p.trip_id, p.timestamp.date()) for p in points}) != 1:
        raise ValueError("Pass one trip ID and date at a time.")
    for first, last in zip(points, points[1:]):
        seconds_between(first, last)
        if last.x_m < first.x_m:
            raise ValueError("This demo requires monotone forward chainage.")
    interior = [
        p for p in points
        if segment.start_m <= p.x_m <= segment.end_m
        and abs(p.y_m) < segment.route_buffer_m
    ]
    if len(interior) < 4:
        raise ValueError("Not enough on-route observations inside the segment.")
    if any(p.y_m != 0 for p in interior):
        raise ValueError("The demo expects map-matched interior points on the corridor.")
    first, last = interior[0], interior[-1]
    before = [p for p in points if p.x_m < segment.start_m]
    after = [p for p in points if p.x_m > segment.end_m]
    if not before or not after:
        raise ValueError("Equation 3 requires observations before and after the segment.")
    preceding, following = before[-1], after[0]
    left = [p for p in interior if p.x_m < segment.stop_center_m - segment.stop_radius_m]
    right = [p for p in interior if p.x_m > segment.stop_center_m + segment.stop_radius_m]
    if len(left) < 2 or len(right) < 2:
        raise ValueError("Need at least two observations on each side of the stop buffer.")
    pre_stop, post_stop = left[-1], right[0]

    # Equation 1: observed time in each non-stop subsegment.
    type1 = seconds_between(left[0], pre_stop) + seconds_between(post_stop, right[-1])

    # Equation 2: actual crossing for skipped stops; imputed crossing for dwell.
    actual = seconds_between(pre_stop, post_stop)
    mean_speed = (pre_stop.speed_mps + post_stop.speed_mps) / 2
    if mean_speed <= 0:
        raise ValueError("Stop-boundary mean speed must be positive for imputation.")
    imputed = (post_stop.x_m - pre_stop.x_m) / mean_speed
    dwelled = actual - imputed >= segment.dwell_threshold_s
    type2 = imputed if dwelled else actual

    # Equation 3: allocate the time gaps spanning the segment boundaries.
    type3 = (
        seconds_between(preceding, first)
        * (first.x_m - segment.start_m) / (first.x_m - preceding.x_m)
        + seconds_between(last, following)
        * (segment.end_m - last.x_m) / (following.x_m - last.x_m)
    )
    observed = seconds_between(first, last) + type3
    return TripEstimate(
        first.trip_id, first.timestamp.date().isoformat(), segment.segment_id,
        first.timestamp, type1, type2, type3, actual, imputed, dwelled, observed,
    )


def aggregate_space_mean_speed(
    estimates: list[TripEstimate], segment: Segment, interval_minutes: int = 15
) -> list[dict[str, object]]:
    """Algorithm 2: total trip distance / total corrected travel time.

    Trips are assigned by their first observation inside the segment, matching
    the published algorithm. Empty intervals are omitted rather than set to 0.
    """
    if interval_minutes <= 0 or 1440 % interval_minutes:
        raise ValueError("Use a positive interval length dividing a 24-hour day.")
    groups: dict[datetime, list[TripEstimate]] = defaultdict(list)
    for estimate in estimates:
        if estimate.segment_id != segment.segment_id:
            raise ValueError("Cannot aggregate estimates from different segments.")
        if estimate.corrected_time_s <= 0:
            raise ValueError("Corrected travel time must be positive.")
        time = estimate.first_timestamp
        midnight = time.replace(hour=0, minute=0, second=0, microsecond=0)
        index = int((time - midnight).total_seconds() // (interval_minutes * 60))
        groups[midnight + timedelta(minutes=index * interval_minutes)].append(estimate)
    result = []
    for interval, trips in sorted(groups.items()):
        total_time = sum(trip.corrected_time_s for trip in trips)
        speed = len(trips) * segment.length_m / total_time
        result.append({
            "interval_start": interval.isoformat(), "trip_count": len(trips),
            "total_corrected_time_s": round(total_time, 6),
            "space_mean_speed_mps": round(speed, 6),
            "space_mean_speed_kph": round(speed * 3.6, 6),
        })
    return result


def synthetic_trip(trip_id: str, start: datetime, speed_mps: float, dwell_s: float):
    """Invent deterministic observations; no empirical records are used."""
    if speed_mps <= 0 or dwell_s < 0:
        raise ValueError("Synthetic speed must be positive and dwell nonnegative.")
    result = []
    for x in (-20, 20, 200, 470, 490, 500, 510, 530, 800, 980, 1020):
        seconds = (x + 20) / speed_mps + (dwell_s if x > 500 else 0)
        result.append(Observation(trip_id, start + timedelta(seconds=seconds), x, 0, speed_mps))
        if x == 500 and dwell_s:
            result.append(Observation(trip_id, start + timedelta(seconds=seconds + dwell_s), x, 0, 0))
    return result


def run_demo() -> dict[str, object]:
    segment = Segment()
    observations = synthetic_trip("bus-A", datetime(2023, 10, 9, 7), 10, 45)
    observations += synthetic_trip("bus-B", datetime(2023, 10, 9, 7, 5), 5, 0)
    # An invented out-of-buffer point demonstrates the route filter.
    observations.append(Observation("off-route", datetime(2023, 10, 9, 7), 500, 100, 10))
    trips = extract_segment_trips(observations, segment)
    estimates = [estimate_trip(points, segment) for points in trips.values()]
    summaries = []
    for trip in estimates:
        summaries.append({
            "trip_id": trip.trip_id, "service_date": trip.service_date,
            "dwell_detected": trip.dwelled, "type1_s": round(trip.type1_s, 6),
            "type2_s": round(trip.type2_s, 6), "type3_s": round(trip.type3_s, 6),
            "actual_stop_crossing_s": round(trip.actual_stop_crossing_s, 6),
            "imputed_stop_crossing_s": round(trip.imputed_stop_crossing_s, 6),
            "observed_segment_time_s": round(trip.observed_segment_time_s, 6),
            "corrected_segment_time_s": round(trip.corrected_time_s, 6),
        })
    return {
        "scope": "Synthetic illustration of published Equations 1–4 and Algorithms 1–2; not publication reproduction.",
        "units": {"position": "metres", "time": "seconds", "speed": "metres/second"},
        "input_observations": len(observations), "retained_trips": len(trips),
        "trips": summaries, "intervals": aggregate_space_mean_speed(estimates, segment),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(run_demo(), indent=2))


if __name__ == "__main__":
    main()
