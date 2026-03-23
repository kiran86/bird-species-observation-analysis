from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"

st.set_page_config(page_title="Bird Observation Dashboard", layout="wide")
st.title("Bird Species Observation Dashboard")
st.caption("Forest and grassland monitoring summary built from the cleaned project dataset.")

data = pd.read_csv(OUTPUT_DIR / "cleaned_bird_observations.csv", parse_dates=["date"])
event_summary = pd.read_csv(OUTPUT_DIR / "survey_event_summary.csv", parse_dates=["date"])

habitats = st.multiselect(
    "Filter habitat",
    sorted(data["habitat_type"].dropna().unique()),
    default=sorted(data["habitat_type"].dropna().unique()),
)

filtered = data[data["habitat_type"].isin(habitats)]
filtered_events = event_summary[event_summary["habitat_type"].isin(habitats)]

col1, col2, col3 = st.columns(3)
col1.metric("Observations", f"{len(filtered):,}")
col2.metric("Species", f"{filtered['common_name'].nunique():,}")
col3.metric("Survey Events", f"{filtered_events['survey_event_id'].nunique():,}")

habitat_counts = (
    filtered.groupby("habitat_type", dropna=False)["observation_id"]
    .count()
    .reset_index(name="total_observations")
)
st.plotly_chart(
    px.bar(habitat_counts, x="habitat_type", y="total_observations", color="habitat_type"),
    use_container_width=True,
)

top_species = (
    filtered.groupby(["habitat_type", "common_name"], dropna=False)["observation_id"]
    .count()
    .reset_index(name="total_observations")
    .sort_values("total_observations", ascending=False)
    .groupby("habitat_type", group_keys=False)
    .head(10)
)
st.plotly_chart(
    px.bar(
        top_species,
        x="total_observations",
        y="common_name",
        color="habitat_type",
        barmode="group",
        title="Top Species by Habitat",
    ),
    use_container_width=True,
)

monthly = (
    filtered.dropna(subset=["observation_year_month"])
    .groupby(["observation_year_month", "habitat_type"], dropna=False)["observation_id"]
    .count()
    .reset_index(name="total_observations")
)
st.plotly_chart(
    px.line(
        monthly,
        x="observation_year_month",
        y="total_observations",
        color="habitat_type",
        markers=True,
        title="Monthly Observation Trend",
    ),
    use_container_width=True,
)

st.plotly_chart(
    px.scatter(
        filtered_events,
        x="temperature",
        y="bird_observation_count",
        color="habitat_type",
        hover_data=["admin_unit_code", "plot_name", "observer"],
        title="Temperature vs Bird Observations",
    ),
    use_container_width=True,
)
