from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
HABITAT_COLORS = {"Forest": "#2D6A4F", "Grassland": "#BC6C25"}


def apply_base_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --dashboard-text: var(--text-color);
            --dashboard-bg: var(--background-color);
            --dashboard-surface: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
            --dashboard-surface-strong: color-mix(in srgb, var(--secondary-background-color) 96%, var(--background-color));
            --dashboard-border: color-mix(in srgb, var(--text-color) 14%, transparent);
            --dashboard-shadow: color-mix(in srgb, black 14%, transparent);
            --dashboard-muted: color-mix(in srgb, var(--text-color) 68%, var(--background-color));
            --dashboard-kicker: color-mix(in srgb, var(--primary-color) 72%, var(--text-color));
        }
        .stApp {
            background:
                radial-gradient(circle at top left, color-mix(in srgb, var(--primary-color) 18%, transparent), transparent 30%),
                radial-gradient(circle at top right, color-mix(in srgb, #BC6C25 18%, transparent), transparent 26%),
                linear-gradient(
                    180deg,
                    color-mix(in srgb, var(--dashboard-bg) 94%, white 6%) 0%,
                    var(--dashboard-bg) 56%,
                    color-mix(in srgb, var(--secondary-background-color) 84%, var(--dashboard-bg)) 100%
                );
        }
        .hero-card, .insight-card {
            background: var(--dashboard-surface);
            border: 1px solid var(--dashboard-border);
            border-radius: 18px;
            padding: 1.1rem 1rem;
            box-shadow: 0 14px 30px var(--dashboard-shadow);
            backdrop-filter: blur(10px);
        }
        .insight-card {
            min-height: 132px;
        }
        .metric-label {
            color: var(--dashboard-muted);
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-value {
            color: var(--dashboard-text);
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
        }
        .metric-subtle {
            color: var(--dashboard-muted);
            font-size: 0.9rem;
            margin-top: 0.3rem;
        }
        .section-kicker {
            color: var(--dashboard-kicker);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
        [data-testid="stHeading"] {
            color: var(--dashboard-text);
        }
        [data-testid="stCaptionContainer"] {
            color: var(--dashboard-muted);
        }
        [data-testid="stSidebar"] {
            background: color-mix(in srgb, var(--secondary-background-color) 94%, var(--background-color));
        }
        [data-testid="stSidebar"] * {
            color: var(--dashboard-text);
        }
        .js-plotly-plot, .js-plotly-plot .plot-container {
            border-radius: 18px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def configure_page(title: str) -> None:
    st.set_page_config(page_title=title, layout="wide")
    apply_base_style()


@st.cache_data(show_spinner=False)
def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    observations = pd.read_csv(
        OUTPUT_DIR / "cleaned_bird_observations.csv",
        parse_dates=["date"],
    )
    events = pd.read_csv(
        OUTPUT_DIR / "survey_event_summary.csv",
        parse_dates=["date"],
    )

    bool_like_columns = [
        "flyover_observed",
        "pif_watchlist_status",
        "regional_stewardship_status",
        "initial_three_min_cnt",
        "previously_obs",
    ]
    for frame in (observations, events):
        for column in frame.columns:
            if frame[column].dtype == object:
                frame[column] = frame[column].replace({"True": True, "False": False})
        for column in bool_like_columns:
            if column in frame.columns:
                frame[column] = frame[column].astype("boolean")

    observations["observation_year_month"] = observations[
        "observation_year_month"
    ].astype("string")
    observations["month_start"] = pd.to_datetime(
        observations["observation_year_month"] + "-01",
        errors="coerce",
    )
    observations["distance_band"] = observations["distance"].fillna("Unknown")
    observations["sex_label"] = observations["sex"].fillna("Unknown")
    observations["observer"] = observations["observer"].fillna("Unknown")

    events["month_start"] = events["date"].dt.to_period("M").dt.to_timestamp()
    events["temperature_band"] = pd.cut(
        events["temperature"],
        bins=[-100, 10, 15, 20, 25, 30, 100],
        labels=["<=10C", "10-15C", "15-20C", "20-25C", "25-30C", "30C+"],
    )
    events["start_hour"] = (
        pd.to_datetime(events["survey_event_id"].str.split("|").str[4], errors="coerce")
        .dt.hour
    )

    return observations, events


def inject_sidebar_filters(observations: pd.DataFrame) -> dict[str, list]:
    st.sidebar.header("Filters")

    habitats = sorted(observations["habitat_type"].dropna().unique().tolist())
    selected_habitats = st.sidebar.multiselect(
        "Habitat",
        habitats,
        default=habitats,
    )

    months = (
        observations[["observation_year_month", "month_start"]]
        .dropna()
        .drop_duplicates()
        .sort_values("month_start")
    )
    month_labels = months["observation_year_month"].tolist()
    selected_months = st.sidebar.multiselect(
        "Month",
        month_labels,
        default=month_labels,
    )

    observers = sorted(observations["observer"].dropna().unique().tolist())
    selected_observers = st.sidebar.multiselect(
        "Observer",
        observers,
        default=observers,
    )

    if not selected_observers:
        selected_observers = observers

    return {
        "habitats": selected_habitats or habitats,
        "months": selected_months or month_labels,
        "observers": selected_observers,
    }


def filter_observations(
    observations: pd.DataFrame,
    filters: dict[str, list],
) -> pd.DataFrame:
    filtered = observations.copy()
    filtered = filtered[filtered["habitat_type"].isin(filters["habitats"])]
    filtered = filtered[filtered["observation_year_month"].isin(filters["months"])]
    filtered = filtered[filtered["observer"].isin(filters["observers"])]
    return filtered


def filter_events(
    events: pd.DataFrame,
    filters: dict[str, list],
) -> pd.DataFrame:
    filtered = events.copy()
    filtered = filtered[filtered["habitat_type"].isin(filters["habitats"])]
    filtered = filtered[
        filtered["month_start"].dt.strftime("%Y-%m").isin(filters["months"])
    ]
    filtered = filtered[filtered["observer"].isin(filters["observers"])]
    return filtered


def metric_card(label: str, value: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def narrative_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="section-kicker">{title}</div>
            <div style="font-size: 1rem; color: var(--dashboard-text); margin-top: 0.4rem;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def styled_plotly(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        legend_title_text="",
    )
    return fig


def habitat_color_sequence(items: Iterable[str]) -> list[str]:
    return [HABITAT_COLORS.get(item, "#6c757d") for item in items]


def habitat_color_map() -> dict[str, str]:
    return HABITAT_COLORS.copy()


def highlight_text(text: str) -> None:
    st.caption(text)


def safe_pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return float(numerator) / float(denominator)


def top_species_by_habitat(observations: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    top_species = (
        observations.groupby(["habitat_type", "common_name"], dropna=False)["observation_id"]
        .count()
        .reset_index(name="observations")
        .sort_values(["habitat_type", "observations"], ascending=[True, False])
    )
    return top_species.groupby("habitat_type", group_keys=False).head(top_n)


def species_presence_matrix(observations: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    matrix_source = (
        observations.groupby(["common_name", "habitat_type"])["observation_id"]
        .count()
        .reset_index(name="observations")
    )
    species_totals = (
        matrix_source.groupby("common_name")["observations"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index
    )
    matrix = (
        matrix_source[matrix_source["common_name"].isin(species_totals)]
        .pivot(index="common_name", columns="habitat_type", values="observations")
        .fillna(0)
    )
    return matrix.sort_values(list(matrix.columns), ascending=False)


def species_mix_summary(observations: pd.DataFrame) -> tuple[str, str]:
    species_by_habitat = observations.groupby("habitat_type")["common_name"].nunique()
    if species_by_habitat.empty:
        return "No species in current filter.", "Expand the filters to recover comparisons."

    leader = species_by_habitat.idxmax()
    lagger = species_by_habitat.idxmin()
    gap = int(species_by_habitat.max() - species_by_habitat.min())

    if len(species_by_habitat) == 1:
        return (
            f"{leader} is the only habitat in scope.",
            f"It contributes {int(species_by_habitat.iloc[0])} distinct species.",
        )

    return (
        f"{leader} is richer by {gap} species.",
        f"{leader} shows {int(species_by_habitat[leader])} species versus {int(species_by_habitat[lagger])} in {lagger}.",
    )


def event_productivity_summary(events: pd.DataFrame) -> tuple[str, str]:
    if events.empty:
        return "No survey events in scope.", "Expand the filters to reveal effort and productivity."

    best = events.sort_values("bird_observation_count", ascending=False).iloc[0]
    return (
        f"{best['plot_name']} was the most productive event.",
        f"{int(best['bird_observation_count'])} detections and {int(best['unique_species_count'])} species were logged on {best['date'].date()}.",
    )


def common_empty_state() -> None:
    st.info("The current filters returned no rows. Adjust the sidebar filters to continue exploring.")
