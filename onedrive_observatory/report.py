import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "report.html"


def build_filter_payload(df: pd.DataFrame, daily_all: pd.Series) -> Dict[str, object]:
    df_known = df[df["date_taken"].notna()].copy()
    df_known["date"] = df_known["date_taken"].dt.strftime("%Y-%m-%d")

    media_types = ["photo", "video"]

    type_index = {v: i for i, v in enumerate(media_types)}

    records = {
        "dates": df_known["date"].tolist(),
        "types": [type_index[v] for v in df_known["media_type"].tolist()],
    }

    payload = {
        "media_types": media_types,
        "records": records,
        "date_list": [d.strftime("%Y-%m-%d") for d in daily_all.index],
    }
    return payload


def render_html(
    stats: Dict[str, object],
    insights: List[str],
    figures: Dict[str, str],
    payload: Dict[str, object],
    template_path: Path = TEMPLATE_PATH,
) -> str:
    coverage_pct = f"{stats['coverage'] * 100:.1f}%"
    peak_day = stats["peak_day"].strftime("%Y-%m-%d") if stats["peak_day"] is not None else "-"
    start_range = stats["start_range"].strftime("%Y-%m-%d") if stats["start_range"] is not None else "-"
    end_range = stats["end_range"].strftime("%Y-%m-%d") if stats["end_range"] is not None else "-"

    payload_json = json.dumps(payload)

    insight_cards = "\n".join(
        [f"<div class=\"insight-card\">{insight}</div>" for insight in insights]
    )

    replacements = {
        "DATE_RANGE": f"{start_range} to {end_range}",
        "PEAK_DAY": peak_day,
        "TOTAL_FILES": str(stats["total_files"]),
        "TOTAL_PHOTOS": str(stats["total_photos"]),
        "TOTAL_VIDEOS": str(stats["total_videos"]),
        "UNIQUE_FILES": str(stats["unique_files"]),
        "DUPLICATES": str(stats["duplicates"]),
        "NEAR_DUP_GROUPS": str(stats["near_dup_groups"]),
        "COVERAGE_PCT": coverage_pct,
        "LONGEST_STREAK": str(stats["longest_streak"]),
        "INSIGHT_CARDS": insight_cards,
        "MEDIAN_ACTIVE": f"{stats['median_active']:.1f}",
        "P90_ACTIVE": f"{stats['p90_active']:.1f}",
        "VELOCITY_30D": f"{stats['velocity_30d']:.2f}/day",
        "VELOCITY_90D": f"{stats['velocity_90d']:.2f}/day",
        "WEEKDAY_PEAK": str(stats["weekday_peak"]),
        "HOUR_PEAK": str(stats["hour_peak"] if stats["hour_peak"] is not None else "-"),
        "MTIME_FALLBACK": str(stats["mtime_fallback"]),
        "PAYLOAD_JSON": payload_json,
        "FIG_DAILY": figures["daily"],
        "FIG_WEEKLY": figures["weekly"],
        "FIG_MONTHLY": figures["monthly"],
        "FIG_STL": figures["stl"],
        "FIG_YOY": figures["yoy"],
        "FIG_SEASON": figures["season"],
        "FIG_HOUR": figures["hour"],
        "FIG_MEDIA": figures["media"],
        "FIG_FILE_TYPES": figures["file_types"],
        "FIG_MARKET_MA": figures["market_ma"],
        "FIG_MARKET_VOLUME": figures["market_volume"],
        "FIG_MARKET_MOMENTUM": figures["market_momentum"],
        "FIG_MARKET_VOLATILITY": figures["market_volatility"],
        "FIG_MARKET_DRAWDOWN": figures["market_drawdown"],
        "FIG_CALENDAR": figures["calendar"],
        "FIG_SMALL": figures["small"],
    }

    html = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        html = html.replace(f"{{{{{key}}}}}", value)

    return html
