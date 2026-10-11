"""Original research excerpts: structured context and purpose-classification messages.
Source: Stay purpose infer - paper version 6.ipynb, cells 16-17 (zero-based).
Rich prompt is selected as in the source. No API calls, keys, data or fine-tuning.
"""
import json
import numpy as np
import pandas as pd

SYSTEM_PROMPT_CONCISE = (
    "You are an expert mobility analyst. "
    "Classify the purpose of a stay segment into exactly one of these categories: "
    "Home, Work/Study, Personal Needs, Recreation/Social, Other/Unknown. "
    "Other/Unknown covers transfers, waiting at transport nodes, and stays that do not "
    "match any of the other four activity types. "
    "Use only the provided structured context. "
    'Output only valid JSON in the form {"purpose": "<one category>"}.'
)

SYSTEM_PROMPT_RICH = (
    "You are an expert human mobility analyst. You are given structured context "
    "about a single stay: one place where a person stopped for a while. "
    "Classify the stay's activity purpose into exactly one of five categories.\n\n"
    "Categories and the signals that indicate them:\n"
    "- Home: the person's residence. Signals: is_near_user_night_anchor = true, "
    "overnight or long stays, nearest_poi_category = residential, high visit_share_same_area.\n"
    "- Work/Study: a workplace or school. Signals: is_near_user_daytime_anchor = true, "
    "repeated weekday daytime presence, nearest_poi_category = workplace or education.\n"
    "- Personal Needs: obtaining goods, services, food, or care. This includes "
    "shopping, errands, medical visits, and dining out or eating. Signals: "
    "nearest_poi_category = commercial_food, daytime, short to medium duration, low recurrence.\n"
    "- Recreation/Social: leisure and social activity by choice, such as visiting family or "
    "friends, socializing, worship, exercise, sports, parks, and entertainment. "
    "Note: dining out and eating are classified as Personal Needs, not here. "
    "Signals: nearest_poi_category = leisure_park, evenings or weekends, longer or variable duration.\n"
    "- Other/Unknown: transfers, waiting at transport nodes, "
    "accompanying or assisting other people, or no clear activity signal. "
    "Signals: nearest_poi_category = transit, very short duration, transit POIs nearby.\n\n"
    "Decision order, stop at the first that applies:\n"
    "1. At the user's home anchor -> Home.\n"
    "2. Else at the user's work/study anchor -> Work/Study.\n"
    "3. Else choose between Personal Needs and Recreation/Social. Commercial or food "
    "POIs, shopping, errands, and dining indicate Personal Needs. Parks, sports, and "
    "social or family visits indicate Recreation/Social. If tied, prefer Personal Needs.\n"
    "4. A transport node or no resolvable signal -> Other/Unknown.\n\n"
    "Use only the provided structured context. Do not explain. "
    'Output only valid JSON in the form {"purpose": "<one category>"}.'
)

USE_RICH_PROMPT = True

SYSTEM_PROMPT = SYSTEM_PROMPT_RICH if USE_RICH_PROMPT else SYSTEM_PROMPT_CONCISE

ALLOWED_PURPOSES = {
    "Home", "Work/Study", "Personal Needs", "Recreation/Social", "Other/Unknown",
}

def safe_value(x):
    if pd.isna(x): return None
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, (pd.Timestamp,)): return x.isoformat()
    return x


def safe_round(x, ndigits=2):
    if pd.isna(x): return None
    try: return round(float(x), ndigits)
    except Exception: return None


def safe_bool(x):
    if pd.isna(x): return None
    return bool(x)


def get_value(row, col, default=None):
    if col not in row.index: return default
    return row[col]


def get_activity_id(row):
    if "activity_id" not in row.index: return None
    val = row["activity_id"]
    if pd.isna(val): return None
    try: return int(val)
    except Exception: return safe_value(val)


def build_stay_context_payload(row):
    payload = {
        "stay_segment": {
            "start_time": safe_value(get_value(row, "start_ts")),
            "end_time": safe_value(get_value(row, "end_ts")),
            "duration_min": safe_round(get_value(row, "duration_min"), 2),
            "duration_hr": safe_round(get_value(row, "duration_hr"), 2),
            "duration_pctile_user": safe_round(get_value(row, "duration_pctile_user"), 3),  # CHANGE ③
            "n_points": safe_value(get_value(row, "n_points")),
            "day_of_week": safe_value(get_value(row, "day_name")),
            "start_hour": safe_value(get_value(row, "start_hour")),
            "end_hour": safe_value(get_value(row, "end_hour")),
            "is_weekend": safe_bool(get_value(row, "is_weekend")),
            "is_overnight": safe_bool(get_value(row, "is_overnight")),
        },
        "spatial_context": {
            "center_lat": safe_round(get_value(row, "center_lat"), 6),
            "center_lon": safe_round(get_value(row, "center_lon"), 6),
            "inside_building": safe_bool(get_value(row, "inside_building")),
            "nearest_poi_category": safe_value(get_value(row, "nearest_poi_category")),
            "top3_poi": get_value(row, "top3_poi"),                                          # CHANGE ③
            "poi_category_entropy_200m": safe_round(get_value(row, "poi_category_entropy_200m"), 3),  # CHANGE ③
            "dist_to_any_poi_m": safe_round(get_value(row, "dist_to_any_poi_m"), 1),
            "dist_to_nearest_building_m": safe_round(get_value(row, "dist_to_nearest_building_m"), 1),
            "dist_to_nearest_road_m": safe_round(get_value(row, "dist_to_nearest_road_m"), 1),
            "dist_to_nearest_transit_m": safe_round(get_value(row, "dist_to_nearest_transit_m"), 1),
            "total_poi_within_100m": safe_value(get_value(row, "total_poi_within_100m")),
            "total_poi_within_200m": safe_value(get_value(row, "total_poi_within_200m")),
            "n_transit_within_200m": safe_value(get_value(row, "n_transit_within_200m")),
            "n_commercial_food_within_200m": safe_value(get_value(row, "n_commercial_food_within_200m")),
            "n_education_within_200m": safe_value(get_value(row, "n_education_within_200m")),
            "n_leisure_park_within_200m": safe_value(get_value(row, "n_leisure_park_within_200m")),
        },
        "user_history_context": {
            "is_near_user_night_anchor": safe_bool(get_value(row, "is_near_user_night_anchor")),
            "is_near_user_daytime_anchor": safe_bool(get_value(row, "is_near_user_daytime_anchor")),
            "dist_to_user_night_anchor_m": safe_round(get_value(row, "dist_to_user_night_anchor_m"), 1),
            "dist_to_user_daytime_anchor_m": safe_round(get_value(row, "dist_to_user_daytime_anchor_m"), 1),
            "visit_count_same_area_100m": safe_value(get_value(row, "visit_count_same_area_100m")),
            "visit_share_same_area": safe_round(get_value(row, "visit_share_same_area"), 3),  # CHANGE ③
            "same_place_seen_at_night": safe_bool(get_value(row, "same_place_seen_at_night")),
            "same_place_seen_on_weekdays": safe_bool(get_value(row, "same_place_seen_on_weekdays")),
        },
        "trajectory_context": {
            "is_first_stay_for_user": safe_bool(get_value(row, "is_first_stay_for_user")),
            "is_last_stay_for_user": safe_bool(get_value(row, "is_last_stay_for_user")),
            "prev_duration_min": (None if pd.isna(get_value(row, "prev_duration_s"))
                                  else safe_round(get_value(row, "prev_duration_s")/60, 2)),
            "next_duration_min": (None if pd.isna(get_value(row, "next_duration_s"))
                                  else safe_round(get_value(row, "next_duration_s")/60, 2)),
            "travel_time_from_prev_min": (None if pd.isna(get_value(row, "travel_time_from_prev_s"))
                                          else safe_round(get_value(row, "travel_time_from_prev_s")/60, 2)),
            "travel_time_to_next_min": (None if pd.isna(get_value(row, "travel_time_to_next_s"))
                                        else safe_round(get_value(row, "travel_time_to_next_s")/60, 2)),
            "distance_from_prev_stay_m": safe_round(get_value(row, "distance_from_prev_stay_m"), 1),
            "distance_to_next_stay_m": safe_round(get_value(row, "distance_to_next_stay_m"), 1),
            "prev_nearest_poi_category": safe_value(get_value(row, "prev_nearest_poi_category")),
            "next_nearest_poi_category": safe_value(get_value(row, "next_nearest_poi_category")),
        },
    }
    return payload


def build_messages(row, include_label=True):
    user_content = json.dumps(build_stay_context_payload(row), ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    if include_label:
        purpose = get_value(row, "purpose_category")
        if pd.isna(purpose):
            raise ValueError("include_label=True but purpose_category is missing.")
        if purpose not in ALLOWED_PURPOSES:
            raise ValueError(f"Invalid purpose_category: {purpose}")
        messages.append({"role": "assistant",
                         "content": json.dumps({"purpose": purpose}, ensure_ascii=False)})
    return messages
