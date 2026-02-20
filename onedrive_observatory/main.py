from datetime import datetime

import pandas as pd

from .analysis import build_insights, build_stats, build_time_series, find_near_duplicates
from .charts import make_figures
from .config import DEFAULT_SETTINGS, Settings
from .report import build_filter_payload, render_html
from .scanner import scan_media

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


def prompt_hashing(default_enabled: bool) -> bool:
    default_hint = "Y/n" if default_enabled else "y/N"
    while True:
        choice = input(f"Enable hashing (sha1 + dHash)? [{default_hint}]: ").strip().lower()
        if not choice:
            return default_enabled
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Please enter y or n.")


def run(settings: Settings = DEFAULT_SETTINGS) -> None:
    if not settings.base_folder.exists():
        raise SystemExit(f"Base folder not found: {settings.base_folder}")

    start_date = datetime.strptime(settings.start_date, "%Y%m%d").date()
    enable_hashing = settings.enable_hashing
    if settings.prompt_hashing:
        enable_hashing = prompt_hashing(settings.enable_hashing)

    records = scan_media(settings.base_folder, start_date, settings.allowed_years, enable_hashing)

    df = pd.DataFrame([r.__dict__ for r in records])
    if df.empty:
        raise SystemExit("No media found. Check BASE_FOLDER and START_DATE.")

    df = drop_sensitive_columns(df)
    df["date_taken"] = pd.to_datetime(df["date_taken"])

    if enable_hashing:
        df = find_near_duplicates(
            df,
            threshold=settings.near_dup_threshold,
            prefix_len=settings.near_dup_prefix_len,
        )
        df["is_duplicate"] = df.duplicated(subset=["sha1"], keep="first")
    else:
        df["near_dup_group"] = None
        df["is_duplicate"] = False

    series = build_time_series(df, enable_hashing)
    stats = build_stats(df, series, enable_hashing)
    insights = build_insights(df, stats, series)
    figures = make_figures(df, series)
    payload = build_filter_payload(df, series["daily_all"])

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.output_csv, index=False)

    html = render_html(stats, insights, figures, payload)
    settings.output_html.write_text(html, encoding="utf-8")

    print(f"Report written to {settings.output_html}")
    print(f"Data exported to {settings.output_csv}")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
