from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_utils import (
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
    safe_pct,
    species_mix_summary,
    species_presence_matrix,
    styled_plotly,
    top_species_by_habitat,
)


configure_page("Bird Observation Dashboard")
observations, events = load_dashboard_data()
filters = inject_sidebar_filters(observations)
filtered_obs = filter_observations(observations, filters)
filtered_events = filter_events(events, filters)

st.title("Bird Observation Intelligence Hub")
st.caption(
    "A multipage Streamlit experience for comparing habitat performance, exploring species signals, and understanding when survey conditions produce the strongest bird detections."
)

if filtered_obs.empty or filtered_events.empty:
    common_empty_state()
    st.stop()

species_headline, species_detail = species_mix_summary(filtered_obs)
productivity_headline, productivity_detail = event_productivity_summary(filtered_events)

left, right = st.columns([1.2, 1])
with left:
    narrative_card(
        "What stands out",
        f"<strong>{species_headline}</strong> {species_detail}",
    )
with right:
    narrative_card(
        "Best field result",
        f"<strong>{productivity_headline}</strong> {productivity_detail}",
    )

total_observations = len(filtered_obs)
total_species = filtered_obs["common_name"].nunique()
total_events = filtered_events["survey_event_id"].nunique()
avg_species_per_event = filtered_events["unique_species_count"].mean()
watchlist_share = safe_pct(
    filtered_obs["pif_watchlist_status"].fillna(False).sum(),
    total_observations,
)

metric_cols = st.columns(5)
with metric_cols[0]:
    metric_card("Observations", f"{total_observations:,}", "Bird detections in current scope")
with metric_cols[1]:
    metric_card("Species", f"{total_species:,}", "Distinct common names observed")
with metric_cols[2]:
    metric_card("Survey events", f"{total_events:,}", "Unique field survey sessions")
with metric_cols[3]:
    metric_card("Species per event", f"{avg_species_per_event:.1f}", "Average richness per survey")
with metric_cols[4]:
    metric_card("Watchlist share", f"{watchlist_share:.1%}", "Portion flagged by PIF watchlist")

st.markdown("### Snapshot")
snapshot_left, snapshot_right = st.columns([1.2, 1])

with snapshot_left:
    habitat_rollup = (
        filtered_obs.groupby("habitat_type")
        .agg(
            observations=("observation_id", "count"),
            species=("common_name", "nunique"),
            watchlist=("pif_watchlist_status", lambda s: s.fillna(False).sum()),
        )
        .reset_index()
    )
    habitat_rollup["watchlist_share"] = habitat_rollup["watchlist"] / habitat_rollup["observations"]
    fig = px.bar(
        habitat_rollup,
        x="habitat_type",
        y=["observations", "species"],
        barmode="group",
        color_discrete_sequence=["#2D6A4F", "#DDA15E"],
        title="Volume and richness by habitat",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with snapshot_right:
    monthly = (
        filtered_obs.dropna(subset=["month_start"])
        .groupby(["month_start", "habitat_type"])["observation_id"]
        .count()
        .reset_index(name="observations")
    )
    fig = px.area(
        monthly,
        x="month_start",
        y="observations",
        color="habitat_type",
        color_discrete_map=habitat_color_map(),
        markers=True,
        title="Observation momentum over time",
    )
    fig.update_traces(mode="lines+markers")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Community composition")
mix_left, mix_right = st.columns([1.05, 1.15])

with mix_left:
    top_species = top_species_by_habitat(filtered_obs, top_n=7)
    fig = px.bar(
        top_species,
        x="observations",
        y="common_name",
        color="habitat_type",
        facet_col="habitat_type",
        facet_col_spacing=0.08,
        color_discrete_map=habitat_color_map(),
        title="Most frequently observed species by habitat",
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with mix_right:
    matrix = species_presence_matrix(filtered_obs, top_n=14)
    fig = px.imshow(
        matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="YlGn",
        title="Shared and concentrated species among the most observed birds",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Survey productivity")
product_left, product_right = st.columns([1.15, 1.05])

with product_left:
    fig = px.scatter(
        filtered_events,
        x="temperature",
        y="bird_observation_count",
        color="habitat_type",
        size="unique_species_count",
        hover_data=["admin_unit_code", "plot_name", "observer", "date"],
        color_discrete_map=habitat_color_map(),
        title="Warmer conditions do not always produce stronger surveys",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with product_right:
    event_mix = (
        filtered_events.groupby("habitat_type")
        .agg(
            avg_birds=("bird_observation_count", "mean"),
            avg_species=("unique_species_count", "mean"),
            avg_temp=("temperature", "mean"),
        )
        .reset_index()
    )
    fig = px.scatter(
        event_mix,
        x="avg_temp",
        y="avg_birds",
        color="habitat_type",
        size="avg_species",
        text="habitat_type",
        color_discrete_map=habitat_color_map(),
        title="Habitat-level event efficiency",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

highlight_text(
    "Use the pages in the sidebar for deeper habitat comparisons, species-level exploration, and condition-driven survey analysis."
)
