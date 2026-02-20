import sys
from pathlib import Path

import pandas as pd

from .analysis import build_insights, build_stats, build_time_series, find_near_duplicates
from .charts import make_figures
from .config import DEFAULT_SETTINGS, Settings
from .report import build_filter_payload, render_html

SENSITIVE_COLUMNS = {
    "path",
    "name",
    "device",
    "make",
    "model",
    "lens",
    "gps_lat",
    "gps_lon",
    "location_bucket",
}


def drop_sensitive_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in SENSITIVE_COLUMNS if c in df.columns], errors="ignore")


def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "date_taken" in df.columns:
        df["date_taken"] = pd.to_datetime(df["date_taken"], errors="coerce")
    if "mtime" in df.columns:
        df["mtime"] = pd.to_datetime(df["mtime"], errors="coerce")
    if "ext" in df.columns:
        df["ext"] = df["ext"].fillna("unknown").astype(str).str.lower()
    return df


def apply_filename_time_fallback(df: pd.DataFrame) -> pd.DataFrame:
    if "date_source" not in df.columns:
        return df
    if "mtime" not in df.columns or "date_taken" not in df.columns:
        return df
    mask = df["date_source"] == "filename"
    if mask.any():
        df.loc[mask, "date_taken"] = df.loc[mask, "date_taken"].dt.normalize() + (
            df.loc[mask, "mtime"] - df.loc[mask, "mtime"].dt.normalize()
        )
    return df


def run_from_csv(csv_path: Path, settings: Settings = DEFAULT_SETTINGS) -> None:
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    df = load_csv(csv_path)
    df = drop_sensitive_columns(df)
    df = apply_filename_time_fallback(df)

    if "sha1" in df.columns:
        hashing_enabled = df["sha1"].notna().any()
    else:
        hashing_enabled = False

    if "near_dup_group" not in df.columns:
        if hashing_enabled and "dhash" in df.columns:
            df = find_near_duplicates(
                df,
                threshold=settings.near_dup_threshold,
                prefix_len=settings.near_dup_prefix_len,
            )
        else:
            df["near_dup_group"] = None

    if "is_duplicate" not in df.columns:
        if hashing_enabled and "sha1" in df.columns:
            df["is_duplicate"] = df.duplicated(subset=["sha1"], keep="first")
        else:
            df["is_duplicate"] = False

    series = build_time_series(df, hashing_enabled)
    stats = build_stats(df, series, hashing_enabled)
    insights = build_insights(df, stats, series)
    figures = make_figures(df, series)
    payload = build_filter_payload(df, series["daily_all"])

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    html = render_html(stats, insights, figures, payload)
    settings.output_html.write_text(html, encoding="utf-8")

    print(f"Report written to {settings.output_html}")


def main() -> None:
    csv_path = None
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = DEFAULT_SETTINGS.default_csv_path

    run_from_csv(csv_path)


if __name__ == "__main__":
    main()
