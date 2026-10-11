"""Original research excerpts: stay segments and temporal IoU evaluation.
Source: MIT_Stay_algorithm-AllUsers.ipynb, code cells 84, 87, 88 (zero-based).
Function bodies are preserved; imports made explicit.
"""
import numpy as np
import pandas as pd

def point_labels_to_segments(
    df,
    user_col="user_id",
    time_col="tracked_at",
    lat_col="latitude",
    lon_col="longitude",
    pred_col="pred_label",
    prob_col="pred_stay_prob",
    min_duration_s=300,
    max_gap_within_segment_s=1800,
):
    segments = []

    df = df.sort_values([user_col, time_col]).copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    for user_id, sub in df.groupby(user_col, sort=False):
        sub = sub.reset_index(drop=False)

        labels = sub[pred_col].fillna(0).astype(int).to_numpy()
        times = sub[time_col].to_numpy()

        start = None

        for i in range(len(sub)):
            current_is_stay = labels[i] == 1

            if i == 0:
                gap_from_prev = 0
            else:
                gap_from_prev = (
                    pd.Timestamp(times[i]) - pd.Timestamp(times[i - 1])
                ).total_seconds()

            gap_break = gap_from_prev > max_gap_within_segment_s

            if gap_break and start is not None:
                end = i - 1
                seg = sub.iloc[start:end + 1]

                start_time = seg[time_col].iloc[0]
                end_time = seg[time_col].iloc[-1]
                duration_s = (end_time - start_time).total_seconds()

                if duration_s >= min_duration_s:
                    segments.append({
                        "user_id": user_id,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_s": duration_s,
                        "n_points": len(seg),
                        "centroid_lat": seg[lat_col].mean(),
                        "centroid_lon": seg[lon_col].mean(),
                        "start_lat": seg[lat_col].iloc[0],
                        "start_lon": seg[lon_col].iloc[0],
                        "end_lat": seg[lat_col].iloc[-1],
                        "end_lon": seg[lon_col].iloc[-1],
                        "mean_stay_prob": seg[prob_col].mean() if prob_col in seg else np.nan,
                        "max_stay_prob": seg[prob_col].max() if prob_col in seg else np.nan,
                        "min_stay_prob": seg[prob_col].min() if prob_col in seg else np.nan,
                    })

                start = None

            if current_is_stay and start is None:
                start = i

            if (not current_is_stay) and start is not None:
                end = i - 1
                seg = sub.iloc[start:end + 1]

                start_time = seg[time_col].iloc[0]
                end_time = seg[time_col].iloc[-1]
                duration_s = (end_time - start_time).total_seconds()

                if duration_s >= min_duration_s:
                    segments.append({
                        "user_id": user_id,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_s": duration_s,
                        "n_points": len(seg),
                        "centroid_lat": seg[lat_col].mean(),
                        "centroid_lon": seg[lon_col].mean(),
                        "start_lat": seg[lat_col].iloc[0],
                        "start_lon": seg[lon_col].iloc[0],
                        "end_lat": seg[lat_col].iloc[-1],
                        "end_lon": seg[lon_col].iloc[-1],
                        "mean_stay_prob": seg[prob_col].mean() if prob_col in seg else np.nan,
                        "max_stay_prob": seg[prob_col].max() if prob_col in seg else np.nan,
                        "min_stay_prob": seg[prob_col].min() if prob_col in seg else np.nan,
                    })

                start = None

        if start is not None:
            seg = sub.iloc[start:]

            start_time = seg[time_col].iloc[0]
            end_time = seg[time_col].iloc[-1]
            duration_s = (end_time - start_time).total_seconds()

            if duration_s >= min_duration_s:
                segments.append({
                    "user_id": user_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_s": duration_s,
                    "n_points": len(seg),
                    "centroid_lat": seg[lat_col].mean(),
                    "centroid_lon": seg[lon_col].mean(),
                    "start_lat": seg[lat_col].iloc[0],
                    "start_lon": seg[lon_col].iloc[0],
                    "end_lat": seg[lat_col].iloc[-1],
                    "end_lon": seg[lon_col].iloc[-1],
                    "mean_stay_prob": seg[prob_col].mean() if prob_col in seg else np.nan,
                    "max_stay_prob": seg[prob_col].max() if prob_col in seg else np.nan,
                    "min_stay_prob": seg[prob_col].min() if prob_col in seg else np.nan,
                })

    return pd.DataFrame(segments)


def temporal_iou(seg_a, seg_b):
    start_a = pd.Timestamp(seg_a["start_time"])
    end_a = pd.Timestamp(seg_a["end_time"])
    start_b = pd.Timestamp(seg_b["start_time"])
    end_b = pd.Timestamp(seg_b["end_time"])

    inter_start = max(start_a, start_b)
    inter_end = min(end_a, end_b)

    intersection = max((inter_end - inter_start).total_seconds(), 0)

    union_start = min(start_a, start_b)
    union_end = max(end_a, end_b)

    union = max((union_end - union_start).total_seconds(), 1e-9)

    return intersection / union


def evaluate_segments_temporal_iou(
    pred_segments,
    true_segments,
    user_col="user_id",
    iou_threshold=0.5,
):
    matches = []

    pred_segments = pred_segments.copy().reset_index(drop=True)
    true_segments = true_segments.copy().reset_index(drop=True)

    pred_segments["pred_seg_id"] = pred_segments.index
    true_segments["true_seg_id"] = true_segments.index

    matched_pred = set()
    matched_true = set()

    for user_id in sorted(set(pred_segments[user_col]) | set(true_segments[user_col])):
        pred_u = pred_segments[pred_segments[user_col] == user_id]
        true_u = true_segments[true_segments[user_col] == user_id]

        candidates = []

        for _, p in pred_u.iterrows():
            for _, t in true_u.iterrows():
                # quick overlap check
                if pd.Timestamp(p["end_time"]) < pd.Timestamp(t["start_time"]):
                    continue
                if pd.Timestamp(t["end_time"]) < pd.Timestamp(p["start_time"]):
                    continue

                iou = temporal_iou(p, t)

                if iou >= iou_threshold:
                    candidates.append((iou, p["pred_seg_id"], t["true_seg_id"]))

        # highest IoU first, one-to-one matching
        candidates.sort(reverse=True)

        for iou, pred_id, true_id in candidates:
            if pred_id in matched_pred or true_id in matched_true:
                continue

            matched_pred.add(pred_id)
            matched_true.add(true_id)

            matches.append({
                "user_id": user_id,
                "pred_seg_id": pred_id,
                "true_seg_id": true_id,
                "iou": iou,
            })

    n_pred = len(pred_segments)
    n_true = len(true_segments)
    n_match = len(matches)

    precision = n_match / n_pred if n_pred > 0 else 0
    recall = n_match / n_true if n_true > 0 else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0
    )

    matches_df = pd.DataFrame(matches)

    return {
        "n_pred": n_pred,
        "n_true": n_true,
        "n_match": n_match,
        "segment_precision": precision,
        "segment_recall": recall,
        "segment_f1": f1,
        "mean_matched_iou": matches_df["iou"].mean() if len(matches_df) else np.nan,
        "median_matched_iou": matches_df["iou"].median() if len(matches_df) else np.nan,
        "matches": matches_df,
    }
