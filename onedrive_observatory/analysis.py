from typing import Dict, List, Optional, Tuple

import pandas as pd
from statsmodels.tsa.seasonal import STL


def hamming_distance(hex_a: str, hex_b: str) -> int:
    try:
        a = int(hex_a, 16)
        b = int(hex_b, 16)
        return (a ^ b).bit_count()
    except Exception:
        return 64


def find_near_duplicates(
    df: pd.DataFrame, threshold: int, prefix_len: int
) -> pd.DataFrame:
    df = df.copy()
    df["near_dup_group"] = None
    df_hash = df[df["dhash"].notna()].copy()
    if df_hash.empty:
        return df

    buckets: Dict[str, List[Tuple[int, str]]] = {}
    for idx, row in df_hash.iterrows():
        dhash = row["dhash"]
        prefix = dhash[:prefix_len]
        buckets.setdefault(prefix, []).append((idx, dhash))

    group_id = 0
    for entries in buckets.values():
        if len(entries) < 2:
            continue
        used = set()
        for i, (idx_a, hash_a) in enumerate(entries):
            if idx_a in used:
                continue
            cluster = [idx_a]
            used.add(idx_a)
            for idx_b, hash_b in entries[i + 1 :]:
                if idx_b in used:
                    continue
                if hamming_distance(hash_a, hash_b) <= threshold:
                    cluster.append(idx_b)
                    used.add(idx_b)
            if len(cluster) > 1:
                group_id += 1
                for idx in cluster:
                    df.at[idx, "near_dup_group"] = f"ndup-{group_id:04d}"

    return df


def build_time_series(df: pd.DataFrame, hashing_enabled: bool) -> Dict[str, pd.Series]:
    df_known = df[df["date_taken"].notna()].copy()
    df_known["date"] = df_known["date_taken"].dt.floor("D")
    min_date = df_known["date"].min()
    max_date = df_known["date"].max()
    date_range = pd.date_range(min_date, max_date, freq="D")

    daily_all = df_known.groupby("date").size().reindex(date_range, fill_value=0)
    if hashing_enabled:
        daily_unique = (
            df_known.drop_duplicates(subset=["sha1"]).groupby("date").size().reindex(date_range, fill_value=0)
        )
    else:
        daily_unique = daily_all.copy()

    weekly_all = daily_all.resample("W-MON").sum()
    monthly_all = daily_all.resample("MS").sum()

    return {
        "daily_all": daily_all,
        "daily_unique": daily_unique,
        "weekly_all": weekly_all,
        "monthly_all": monthly_all,
    }


def compute_streaks(daily_series: pd.Series) -> Tuple[int, int]:
    longest_streak = 0
    longest_gap = 0
    current_streak = 0
    current_gap = 0
    for count in daily_series:
        if count > 0:
            current_streak += 1
            current_gap = 0
            longest_streak = max(longest_streak, current_streak)
        else:
            current_gap += 1
            current_streak = 0
            longest_gap = max(longest_gap, current_gap)
    return longest_streak, longest_gap


def build_stats(
    df: pd.DataFrame, series: Dict[str, pd.Series], hashing_enabled: bool
) -> Dict[str, object]:
    daily_all = series["daily_all"]

    start_range = daily_all.index.min()
    end_range = daily_all.index.max()

    total_files = len(df)
    total_photos = (df["media_type"] == "photo").sum()
    total_videos = (df["media_type"] == "video").sum()
    if hashing_enabled:
        unique_files = df["sha1"].nunique()
        duplicates = total_files - unique_files
        near_dup_files = df["near_dup_group"].notna().sum()
        near_dup_groups = df["near_dup_group"].nunique() if df["near_dup_group"].notna().any() else 0
    else:
        unique_files = total_files
        duplicates = 0
        near_dup_files = 0
        near_dup_groups = 0
    mtime_fallback = (df["date_source"] == "mtime").sum()

    active_days = int((daily_all > 0).sum())
    total_days = len(daily_all)
    coverage = active_days / total_days if total_days else 0.0

    active_counts = daily_all[daily_all > 0]
    median_active = float(active_counts.median()) if not active_counts.empty else 0.0
    p90_active = float(active_counts.quantile(0.9)) if not active_counts.empty else 0.0

    longest_streak, longest_gap = compute_streaks(daily_all)

    peak_day = daily_all.idxmax()
    peak_day_count = int(daily_all.max()) if not daily_all.empty else 0

    weekly_peak = series["weekly_all"].idxmax()
    monthly_peak = series["monthly_all"].idxmax()

    velocity_30d = float(daily_all.tail(30).mean()) if len(daily_all) >= 30 else float(daily_all.mean())
    velocity_90d = float(daily_all.tail(90).mean()) if len(daily_all) >= 90 else float(daily_all.mean())
    velocity_overall = float(daily_all.mean()) if len(daily_all) else 0.0

    weekday_counts = df["date_taken"].dt.day_name().value_counts()
    weekday_peak = weekday_counts.idxmax() if not weekday_counts.empty else "Unknown"

    hour_counts = df["date_taken"].dt.hour.value_counts()
    hour_peak = int(hour_counts.idxmax()) if not hour_counts.empty else None

    return {
        "hashing_enabled": hashing_enabled,
        "start_range": start_range,
        "end_range": end_range,
        "total_files": total_files,
        "total_photos": int(total_photos),
        "total_videos": int(total_videos),
        "unique_files": int(unique_files),
        "duplicates": int(duplicates),
        "near_dup_files": int(near_dup_files),
        "near_dup_groups": int(near_dup_groups),
        "mtime_fallback": int(mtime_fallback),
        "active_days": active_days,
        "total_days": total_days,
        "coverage": coverage,
        "median_active": median_active,
        "p90_active": p90_active,
        "longest_streak": longest_streak,
        "longest_gap": longest_gap,
        "peak_day": peak_day,
        "peak_day_count": peak_day_count,
        "weekly_peak": weekly_peak,
        "monthly_peak": monthly_peak,
        "velocity_30d": velocity_30d,
        "velocity_90d": velocity_90d,
        "velocity_overall": velocity_overall,
        "weekday_peak": weekday_peak,
        "hour_peak": hour_peak,
    }


def stl_decompose(daily_series: pd.Series) -> Optional[pd.DataFrame]:
    if len(daily_series) < 14:
        return None
    try:
        stl = STL(daily_series, period=7, robust=True)
        res = stl.fit()
        return pd.DataFrame(
            {
                "trend": res.trend,
                "seasonal": res.seasonal,
                "resid": res.resid,
            },
            index=daily_series.index,
        )
    except Exception:
        return None


def detect_anomalies(daily_series: pd.Series, stl_df: Optional[pd.DataFrame]) -> pd.Series:
    if stl_df is None:
        return pd.Series(False, index=daily_series.index)
    resid = stl_df["resid"]
    if resid.std() == 0:
        return pd.Series(False, index=daily_series.index)
    z = (resid - resid.mean()) / resid.std(ddof=0)
    return z.abs() > 2.5


def build_insights(df: pd.DataFrame, stats: Dict[str, object], series: Dict[str, pd.Series]) -> List[str]:
    daily_all = series["daily_all"]
    monthly_all = series["monthly_all"]

    insights = []
    insights.append(
        f"Peak day: {stats['peak_day'].date()} with {stats['peak_day_count']} captures."
    )
    insights.append(
        f"Longest streak: {stats['longest_streak']} days; longest gap: {stats['longest_gap']} days."
    )
    if stats["hashing_enabled"]:
        if stats["duplicates"] > 0 or stats["near_dup_files"] > 0:
            insights.append(
                f"Duplicates: {stats['duplicates']} exact, {stats['near_dup_files']} near-duplicate files across {stats['near_dup_groups']} groups."
            )
    else:
        insights.append("Hashing disabled; duplicate metrics assume zero duplicates.")
    if stats["mtime_fallback"] > 0:
        insights.append(
            f"{stats['mtime_fallback']} files used modified time as capture date fallback."
        )
    if len(monthly_all) >= 13:
        last_month = monthly_all.index[-1]
        prev_year = last_month - pd.DateOffset(years=1)
        if prev_year in monthly_all.index and monthly_all.loc[prev_year] > 0:
            yoy = (monthly_all.loc[last_month] - monthly_all.loc[prev_year]) / monthly_all.loc[prev_year]
            insights.append(
                f"YoY change for {last_month.strftime('%b %Y')}: {yoy:+.1%} vs {prev_year.strftime('%b %Y')}."
            )
    insights.append(
        f"Capture velocity: {stats['velocity_30d']:.2f}/day (30d) vs {stats['velocity_overall']:.2f}/day overall."
    )
    if stats["hour_peak"] is not None:
        insights.append(
            f"Most common capture hour: {stats['hour_peak']:02d}:00."
        )
    if stats["weekday_peak"] != "Unknown":
        insights.append(
            f"Most active weekday: {stats['weekday_peak']}."
        )
    return insights
