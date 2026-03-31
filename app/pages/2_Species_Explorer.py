from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dashboard_utils import (  # noqa: E402
    common_empty_state,
    configure_page,
    filter_events,
    filter_observations,
    habitat_color_map,
    highlight_text,
    inject_sidebar_filters,
    load_dashboard_data,
    metric_card,
    narrative_card,
    safe_pct,
    styled_plotly,
)


configure_page("Species Explorer")
observations, events = load_dashboard_data()
filters = inject_sidebar_filters(observations)
filtered_obs = filter_observations(observations, filters)
filtered_events = filter_events(events, filters)

st.title("Species Explorer")
st.caption("Inspect how a single species is distributed across habitats, locations, months, and field conditions.")

if filtered_obs.empty:
    common_empty_state()
    st.stop()

species_options = sorted(filtered_obs["common_name"].dropna().unique().tolist())
default_species = species_options[0] if species_options else None
selected_species = st.selectbox("Choose a species", species_options, index=0 if default_species else None)

species_obs = filtered_obs[filtered_obs["common_name"] == selected_species]
if species_obs.empty:
    common_empty_state()
    st.stop()

species_name = species_obs["scientific_name"].dropna().iloc[0] if species_obs["scientific_name"].notna().any() else "Scientific name unavailable"
watchlist_hits = int(species_obs["pif_watchlist_status"].fillna(False).sum())
stewardship_hits = int(species_obs["regional_stewardship_status"].fillna(False).sum())
habitat_mode = species_obs["habitat_type"].mode().iloc[0]
top_location = species_obs["admin_unit_code"].mode().iloc[0]

narrative_card(
    "Species readout",
    (
        f"<strong>{selected_species}</strong> (<em>{species_name}</em>) appears most often in "
        f"<strong>{habitat_mode}</strong>, with the heaviest concentration at <strong>{top_location}</strong>."
    ),
)

metric_cols = st.columns(4)
with metric_cols[0]:
    metric_card("Detections", f"{len(species_obs):,}", "Observation rows for this species")
with metric_cols[1]:
    metric_card("Habitats", f"{species_obs['habitat_type'].nunique()}", "Habitats where it appears")
with metric_cols[2]:
    metric_card("Locations", f"{species_obs['admin_unit_code'].nunique()}", "Distinct park units")
with metric_cols[3]:
    metric_card(
        "Priority flags",
        f"{watchlist_hits + stewardship_hits:,}",
        "Watchlist + stewardship-tagged detections",
    )

st.markdown("### Distribution")
left, right = st.columns([1.08, 1.12])
with left:
    habitat_mix = (
        species_obs.groupby("habitat_type")["observation_id"]
        .count()
        .reset_index(name="observations")
    )
    habitat_mix["share"] = habitat_mix["observations"] / habitat_mix["observations"].sum()
    fig = px.bar(
        habitat_mix,
        x="habitat_type",
        y="share",
        color="habitat_type",
        text_auto=".1%",
        color_discrete_map=habitat_color_map(),
        title="Habitat split",
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with right:
    monthly = (
        species_obs.dropna(subset=["month_start"])
        .groupby(["month_start", "habitat_type"])["observation_id"]
        .count()
        .reset_index(name="observations")
    )
    fig = px.line(
        monthly,
        x="month_start",
        y="observations",
        color="habitat_type",
        markers=True,
        color_discrete_map=habitat_color_map(),
        title="Monthly detection pattern",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Where and how was it detected?")
detail_left, detail_right = st.columns([1.05, 1.15])
with detail_left:
    locations = (
        species_obs.groupby(["admin_unit_code", "habitat_type"])["observation_id"]
        .count()
        .reset_index(name="observations")
        .sort_values("observations", ascending=False)
        .head(15)
    )
    fig = px.bar(
        locations.sort_values("observations"),
        x="observations",
        y="admin_unit_code",
        color="habitat_type",
        color_discrete_map=habitat_color_map(),
        title="Top locations for this species",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with detail_right:
    method_mix = (
        species_obs.groupby("id_method")["observation_id"]
        .count()
        .reset_index(name="observations")
        .sort_values("observations", ascending=False)
    )
    fig = px.bar(
        method_mix.head(12).sort_values("observations"),
        x="observations",
        y="id_method",
        color="observations",
        color_continuous_scale="YlGn",
        title="Identification method mix",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Field conditions for this species")
species_events = filtered_events[
    filtered_events["survey_event_id"].isin(species_obs["survey_event_id"].unique())
]
conditions_left, conditions_right = st.columns([1.05, 1.15])
with conditions_left:
    fig = px.scatter(
        species_events,
        x="temperature",
        y="unique_species_count",
        size="bird_observation_count",
        color="habitat_type",
        hover_data=["plot_name", "admin_unit_code", "date"],
        color_discrete_map=habitat_color_map(),
        title="Species occurrence within broader event richness",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with conditions_right:
    distance_mix = (
        species_obs.groupby("distance_band")["observation_id"]
        .count()
        .reset_index(name="observations")
        .sort_values("observations", ascending=False)
    )
    fig = px.pie(
        distance_mix.head(6),
        names="distance_band",
        values="observations",
        hole=0.52,
        title="Detection distance profile",
        color_discrete_sequence=["#2D6A4F", "#52796F", "#84A98C", "#DDA15E", "#BC6C25", "#A3B18A"],
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Detail table")
summary_table = (
    species_obs.groupby(["admin_unit_code", "plot_name", "observer", "habitat_type"])
    .agg(
        detections=("observation_id", "count"),
        first_month=("observation_year_month", "min"),
        last_month=("observation_year_month", "max"),
        watchlist_share=("pif_watchlist_status", lambda s: safe_pct(s.fillna(False).sum(), len(s))),
    )
    .reset_index()
    .sort_values("detections", ascending=False)
)
st.dataframe(summary_table, use_container_width=True, hide_index=True)

highlight_text(
    "This page works best for comparing a focal species against the rest of the survey context, not just counting how often it appears."
)
