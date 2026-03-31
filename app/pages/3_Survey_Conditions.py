from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dashboard_utils import (  # noqa: E402
    common_empty_state,
    configure_page,
    event_productivity_summary,
    filter_events,
    filter_observations,
    habitat_color_map,
    highlight_text,
    inject_sidebar_filters,
    load_dashboard_data,
    metric_card,
    narrative_card,
    styled_plotly,
)


configure_page("Survey Conditions")
observations, events = load_dashboard_data()
filters = inject_sidebar_filters(observations)
filtered_obs = filter_observations(observations, filters)
filtered_events = filter_events(events, filters)

st.title("Survey Conditions")
st.caption("Understand how temperature, humidity, start time, and weather align with stronger survey outcomes.")

if filtered_obs.empty or filtered_events.empty:
    common_empty_state()
    st.stop()

headline, detail = event_productivity_summary(filtered_events)
narrative_card("Field takeaway", f"<strong>{headline}</strong> {detail}")

metric_cols = st.columns(4)
with metric_cols[0]:
    metric_card("Avg birds / event", f"{filtered_events['bird_observation_count'].mean():.1f}", "Overall event productivity")
with metric_cols[1]:
    metric_card("Avg species / event", f"{filtered_events['unique_species_count'].mean():.1f}", "Richness across survey sessions")
with metric_cols[2]:
    metric_card("Avg temperature", f"{filtered_events['temperature'].mean():.1f}C", "Mean air temperature during surveys")
with metric_cols[3]:
    metric_card("Avg humidity", f"{filtered_events['humidity'].mean():.1f}%", "Mean humidity during surveys")

st.markdown("### Condition-response views")
left, right = st.columns([1.2, 1])
with left:
    fig = px.scatter(
        filtered_events,
        x="temperature",
        y="bird_observation_count",
        color="habitat_type",
        size="unique_species_count",
        hover_data=["admin_unit_code", "plot_name", "observer", "date", "humidity"],
        color_discrete_map=habitat_color_map(),
        title="Temperature against event productivity",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with right:
    weather_band = (
        filtered_events.groupby(["habitat_type", "temperature_band"], dropna=False)
        .agg(
            avg_birds=("bird_observation_count", "mean"),
            avg_species=("unique_species_count", "mean"),
        )
        .reset_index()
        .dropna(subset=["temperature_band"])
    )
    fig = px.bar(
        weather_band,
        x="temperature_band",
        y="avg_birds",
        color="habitat_type",
        barmode="group",
        color_discrete_map=habitat_color_map(),
        title="Average detections by temperature band",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Timing matters")
timing_left, timing_right = st.columns([1.05, 1.15])
with timing_left:
    hour_heatmap = (
        filtered_events.dropna(subset=["start_hour"])
        .groupby(["start_hour", "habitat_type"])["unique_species_count"]
        .mean()
        .reset_index()
        .pivot(index="start_hour", columns="habitat_type", values="unique_species_count")
        .fillna(0)
    )
    fig = px.imshow(
        hour_heatmap,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale="YlGnBu",
        title="Average species richness by survey start hour",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Start hour")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with timing_right:
    sky_mix = (
        filtered_events.groupby(["sky", "habitat_type"])
        .agg(avg_birds=("bird_observation_count", "mean"))
        .reset_index()
        .sort_values("avg_birds", ascending=False)
    )
    fig = px.bar(
        sky_mix,
        x="avg_birds",
        y="sky",
        color="habitat_type",
        barmode="group",
        color_discrete_map=habitat_color_map(),
        title="Average bird detections by sky conditions",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Observer and plot context")
context_left, context_right = st.columns([1.05, 1.15])
with context_left:
    observer_rank = (
        filtered_events.groupby("observer")
        .agg(
            survey_events=("survey_event_id", "count"),
            avg_birds=("bird_observation_count", "mean"),
            avg_species=("unique_species_count", "mean"),
        )
        .reset_index()
        .sort_values(["survey_events", "avg_birds"], ascending=[False, False])
        .head(15)
    )
    fig = px.scatter(
        observer_rank,
        x="survey_events",
        y="avg_birds",
        size="avg_species",
        text="observer",
        color="avg_species",
        color_continuous_scale="YlGn",
        title="Observer-level effort versus average detections",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with context_right:
    plot_rank = (
        filtered_events.groupby(["plot_name", "habitat_type", "admin_unit_code"])
        .agg(
            avg_birds=("bird_observation_count", "mean"),
            avg_species=("unique_species_count", "mean"),
            survey_events=("survey_event_id", "count"),
        )
        .reset_index()
        .query("survey_events >= 2")
        .sort_values("avg_species", ascending=False)
        .head(20)
    )
    fig = px.scatter(
        plot_rank,
        x="avg_birds",
        y="avg_species",
        size="survey_events",
        color="habitat_type",
        hover_data=["plot_name", "admin_unit_code"],
        color_discrete_map=habitat_color_map(),
        title="Plots with consistently rich survey outcomes",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

highlight_text(
    "These charts help separate raw effort from productive conditions, which makes the dashboard more useful for planning future fieldwork."
)
