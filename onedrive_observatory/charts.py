from typing import Dict

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .analysis import detect_anomalies, stl_decompose

DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

COLORWAY = [
    "#0b7a75",
    "#ff8c42",
    "#d95d39",
    "#1b3b6f",
    "#6b705c",
    "#8f5d5d",
    "#3a86ff",
    "#2a9d8f",
]


def apply_plot_theme(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        colorway=COLORWAY,
        font=dict(family="IBM Plex Sans, Avenir, Gill Sans, Trebuchet MS, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.08)")
    return fig


def make_figures(
    df: pd.DataFrame,
    series: Dict[str, pd.Series],
) -> Dict[str, str]:
    daily_all = series["daily_all"]
    daily_unique = series["daily_unique"]
    weekly_all = series["weekly_all"]
    monthly_all = series["monthly_all"]

    stl_df = stl_decompose(daily_all)
    anomalies = detect_anomalies(daily_all, stl_df)

    fig_daily = go.Figure()
    fig_daily.add_trace(go.Scatter(x=daily_all.index, y=daily_all.values, mode="lines", name="Daily"))
    fig_daily.add_trace(
        go.Scatter(
            x=daily_unique.index,
            y=daily_unique.values,
            mode="lines",
            name="Unique",
            line=dict(dash="dot"),
        )
    )
    fig_daily.add_trace(
        go.Scatter(
            x=daily_all.index,
            y=daily_all.rolling(7, min_periods=1, center=True).mean(),
            mode="lines",
            name="7d avg",
        )
    )
    anomaly_dates = daily_all.index[anomalies]
    if len(anomaly_dates) > 0:
        fig_daily.add_trace(
            go.Scatter(
                x=anomaly_dates,
                y=daily_all.loc[anomaly_dates],
                mode="markers",
                name="Anomaly",
                marker=dict(size=8, color="#ff8c42", line=dict(width=1, color="#d95d39")),
            )
        )
    fig_daily = apply_plot_theme(fig_daily, "Daily activity (all vs unique)")

    ma7 = daily_all.rolling(7, min_periods=1).mean()
    ma30 = daily_all.rolling(30, min_periods=1).mean()
    ma90 = daily_all.rolling(90, min_periods=1).mean()

    fig_market_ma = go.Figure()
    fig_market_ma.add_trace(go.Scatter(x=daily_all.index, y=daily_all.values, mode="lines", name="Daily"))
    fig_market_ma.add_trace(go.Scatter(x=ma7.index, y=ma7.values, mode="lines", name="MA 7"))
    fig_market_ma.add_trace(go.Scatter(x=ma30.index, y=ma30.values, mode="lines", name="MA 30"))
    fig_market_ma.add_trace(go.Scatter(x=ma90.index, y=ma90.values, mode="lines", name="MA 90"))
    fig_market_ma = apply_plot_theme(fig_market_ma, "Moving averages (7/30/90)")

    volume_30d = daily_all.rolling(30, min_periods=1).sum()
    fig_market_volume = make_subplots(specs=[[{"secondary_y": True}]])
    fig_market_volume.add_trace(
        go.Bar(x=daily_all.index, y=daily_all.values, name="Daily volume", opacity=0.65),
        secondary_y=False,
    )
    fig_market_volume.add_trace(
        go.Scatter(x=volume_30d.index, y=volume_30d.values, mode="lines", name="30d volume sum"),
        secondary_y=True,
    )
    fig_market_volume.update_yaxes(title_text="Daily counts", secondary_y=False)
    fig_market_volume.update_yaxes(title_text="30d sum", secondary_y=True, showgrid=False)
    fig_market_volume = apply_plot_theme(fig_market_volume, "Volume (daily + 30d sum)")

    momentum = (ma30 / ma90 - 1.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    fig_market_momentum = go.Figure()
    fig_market_momentum.add_trace(
        go.Scatter(x=momentum.index, y=momentum.values, mode="lines", name="Momentum (30d vs 90d)")
    )
    fig_market_momentum.add_hline(
        y=0,
        line_width=1,
        line_dash="dash",
        line_color="rgba(0,0,0,0.25)",
    )
    fig_market_momentum = apply_plot_theme(fig_market_momentum, "Momentum (30d MA vs 90d MA)")
    fig_market_momentum.update_yaxes(tickformat=".1%")

    volatility = daily_all.rolling(30, min_periods=1).std().fillna(0.0)
    fig_market_volatility = go.Figure()
    fig_market_volatility.add_trace(
        go.Scatter(x=volatility.index, y=volatility.values, mode="lines", name="30d volatility")
    )
    fig_market_volatility = apply_plot_theme(fig_market_volatility, "Volatility (30d rolling std)")

    rolling_peak = ma30.cummax()
    drawdown = (ma30 - rolling_peak) / rolling_peak.replace(0, np.nan)
    drawdown = drawdown.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    fig_market_drawdown = go.Figure()
    fig_market_drawdown.add_trace(
        go.Scatter(x=drawdown.index, y=drawdown.values, mode="lines", name="Drawdown")
    )
    fig_market_drawdown.add_hline(
        y=0,
        line_width=1,
        line_dash="dash",
        line_color="rgba(0,0,0,0.25)",
    )
    fig_market_drawdown = apply_plot_theme(fig_market_drawdown, "Drawdown (from 30d MA peak)")
    fig_market_drawdown.update_yaxes(tickformat=".1%")

    fig_weekly = go.Figure()
    fig_weekly.add_trace(go.Bar(x=weekly_all.index, y=weekly_all.values, name="Weekly"))
    fig_weekly.add_trace(
        go.Scatter(
            x=weekly_all.index,
            y=weekly_all.rolling(4, min_periods=1, center=True).mean(),
            mode="lines",
            name="4w avg",
        )
    )
    fig_weekly = apply_plot_theme(fig_weekly, "Weekly counts")

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(x=monthly_all.index, y=monthly_all.values, name="Monthly"))
    fig_monthly.add_trace(
        go.Scatter(
            x=monthly_all.index,
            y=monthly_all.rolling(3, min_periods=1, center=True).mean(),
            mode="lines",
            name="3m avg",
        )
    )
    fig_monthly = apply_plot_theme(fig_monthly, "Monthly counts")

    if stl_df is not None:
        fig_stl = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04)
        fig_stl.add_trace(go.Scatter(x=stl_df.index, y=stl_df["trend"], name="Trend"), row=1, col=1)
        fig_stl.add_trace(go.Scatter(x=stl_df.index, y=stl_df["seasonal"], name="Seasonal"), row=2, col=1)
        fig_stl.add_trace(go.Scatter(x=stl_df.index, y=stl_df["resid"], name="Residual"), row=3, col=1)
        fig_stl = apply_plot_theme(fig_stl, "STL decomposition")
    else:
        fig_stl = go.Figure()
        fig_stl = apply_plot_theme(fig_stl, "STL decomposition (insufficient data)")

    monthly_df = monthly_all.to_frame("count")
    monthly_df["year"] = monthly_df.index.year
    monthly_df["month"] = monthly_df.index.month
    monthly_df["month_name"] = monthly_df["month"].map(lambda m: MONTH_NAMES[m - 1])
    fig_yoy = px.line(
        monthly_df,
        x="month",
        y="count",
        color="year",
        labels={"month": "Month", "count": "Captures"},
    )
    fig_yoy.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTH_NAMES)
    fig_yoy = apply_plot_theme(fig_yoy, "Year-over-year monthly comparison")

    df_known = df[df["date_taken"].notna()].copy()
    df_known["weekday"] = df_known["date_taken"].dt.day_name()
    df_known["month"] = df_known["date_taken"].dt.month
    heat = (
        df_known.groupby(["weekday", "month"]).size().unstack(fill_value=0).reindex(DOW_ORDER)
    )
    heat = heat.reindex(columns=list(range(1, 13)), fill_value=0)
    fig_season = go.Figure(
        data=go.Heatmap(
            z=heat.values,
            x=[MONTH_NAMES[m - 1] for m in heat.columns],
            y=heat.index,
            colorscale="Sunset",
        )
    )
    fig_season = apply_plot_theme(fig_season, "Seasonality heatmap (weekday vs month)")

    df_known["hour"] = df_known["date_taken"].dt.hour
    hour_heat = (
        df_known.groupby(["weekday", "hour"]).size().unstack(fill_value=0).reindex(DOW_ORDER)
    )
    hour_heat = hour_heat.reindex(columns=list(range(0, 24)), fill_value=0)
    fig_hour = go.Figure(
        data=go.Heatmap(
            z=hour_heat.values,
            x=list(range(0, 24)),
            y=hour_heat.index,
            colorscale="Temps",
        )
    )
    fig_hour = apply_plot_theme(fig_hour, "Time-of-day heatmap (weekday vs hour)")

    media_counts = df["media_type"].value_counts().reset_index()
    media_counts.columns = ["media_type", "count"]
    fig_media = px.pie(
        media_counts,
        names="media_type",
        values="count",
        hole=0.5,
    )
    fig_media = apply_plot_theme(fig_media, "Photos vs videos")

    ext_counts = df["ext"].str.lower().value_counts().reset_index()
    ext_counts.columns = ["ext", "count"]
    fig_file_types = px.bar(
        ext_counts,
        x="ext",
        y="count",
        labels={"ext": "File extension", "count": "Captures"},
    )
    fig_file_types = apply_plot_theme(fig_file_types, "File type distribution")

    years = sorted(df_known["date_taken"].dt.year.unique())
    zmax = daily_all.max() if not daily_all.empty else 0
    fig_calendar = make_subplots(rows=len(years), cols=1, shared_xaxes=False, vertical_spacing=0.08)
    for row_idx, year in enumerate(years, start=1):
        year_start = pd.Timestamp(year=year, month=1, day=1)
        year_end = pd.Timestamp(year=year, month=12, day=31)
        days = pd.date_range(year_start, year_end, freq="D")
        week_index = ((days - year_start).days + year_start.weekday()) // 7
        weekday = [d.weekday() for d in days]
        counts = daily_all.reindex(days, fill_value=0).values
        week_max = week_index.max()
        matrix = np.zeros((7, week_max + 1))
        matrix[:] = np.nan
        for idx, w in enumerate(week_index):
            matrix[weekday[idx], w] = counts[idx]
        fig_calendar.add_trace(
            go.Heatmap(
                z=matrix,
                x=list(range(week_max + 1)),
                y=DOW_ORDER,
                colorscale="YlOrRd",
                zmin=0,
                zmax=zmax,
                showscale=row_idx == 1,
            ),
            row=row_idx,
            col=1,
        )
        fig_calendar.update_yaxes(title_text=str(year), row=row_idx, col=1)
    fig_calendar = apply_plot_theme(fig_calendar, "Calendar heatmap")

    fig_small = px.line(
        monthly_df,
        x="month",
        y="count",
        facet_col="year",
        facet_col_wrap=3,
    )
    fig_small.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTH_NAMES)
    fig_small = apply_plot_theme(fig_small, "Monthly profile by year")

    figures = {
        "daily": fig_daily,
        "weekly": fig_weekly,
        "monthly": fig_monthly,
        "stl": fig_stl,
        "yoy": fig_yoy,
        "season": fig_season,
        "hour": fig_hour,
        "media": fig_media,
        "file_types": fig_file_types,
        "market_ma": fig_market_ma,
        "market_volume": fig_market_volume,
        "market_momentum": fig_market_momentum,
        "market_volatility": fig_market_volatility,
        "market_drawdown": fig_market_drawdown,
        "calendar": fig_calendar,
        "small": fig_small,
    }

    html_blocks = {}
    first = True
    for key, fig in figures.items():
        html_blocks[key] = fig.to_html(
            full_html=False,
            include_plotlyjs="inline" if first else False,
            config={"displayModeBar": False},
        )
        first = False
    return html_blocks
