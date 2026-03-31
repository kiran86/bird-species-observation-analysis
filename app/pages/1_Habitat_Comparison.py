from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dashboard_utils import (  # noqa: E402
    common_empty_state,
    configure_page,
    filter_observations,
    habitat_color_map,
    highlight_text,
    inject_sidebar_filters,
    load_dashboard_data,
    narrative_card,
    safe_pct,
    styled_plotly,
)


configure_page("Habitat Comparison")
observations, _events = load_dashboard_data()
filters = inject_sidebar_filters(observations)
filtered_obs = filter_observations(observations, filters)

st.title("Habitat Comparison")
st.caption("Compare richness, concentration, and conservation signals between forest and grassland observations.")

if filtered_obs.empty:
    common_empty_state()
    st.stop()

habitat_rollup = (
    filtered_obs.groupby("habitat_type")
    .agg(
        observations=("observation_id", "count"),
        species=("common_name", "nunique"),
        locations=("admin_unit_code", "nunique"),
        watchlist=("pif_watchlist_status", lambda s: s.fillna(False).sum()),
        stewardship=("regional_stewardship_status", lambda s: s.fillna(False).sum()),
    )
    .reset_index()
)
habitat_rollup["watchlist_share"] = habitat_rollup.apply(
    lambda row: safe_pct(row["watchlist"], row["observations"]),
    axis=1,
)
habitat_rollup["stewardship_share"] = habitat_rollup.apply(
    lambda row: safe_pct(row["stewardship"], row["observations"]),
    axis=1,
)

if len(habitat_rollup) >= 2:
    habitat_rollup = habitat_rollup.sort_values("species", ascending=False)
    leader = habitat_rollup.iloc[0]
    runner_up = habitat_rollup.iloc[1]
    narrative_card(
        "Signal",
        (
            f"<strong>{leader['habitat_type']}</strong> currently leads by "
            f"{int(leader['species'] - runner_up['species'])} species and "
            f"{int(leader['observations'] - runner_up['observations']):,} observations."
        ),
    )

chart_left, chart_right = st.columns([1.1, 1.1])
with chart_left:
    fig = px.bar(
        habitat_rollup,
        x="habitat_type",
        y=["observations", "species", "locations"],
        barmode="group",
        color_discrete_sequence=["#2D6A4F", "#DDA15E", "#6C8B74"],
        title="Scale of effort and ecological breadth",
    )
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with chart_right:
    share_chart = habitat_rollup.melt(
        id_vars="habitat_type",
        value_vars=["watchlist_share", "stewardship_share"],
        var_name="signal_type",
        value_name="share",
    )
    share_chart["signal_type"] = share_chart["signal_type"].map(
        {
            "watchlist_share": "PIF watchlist share",
            "stewardship_share": "Regional stewardship share",
        }
    )
    fig = px.bar(
        share_chart,
        x="signal_type",
        y="share",
        color="habitat_type",
        barmode="group",
        color_discrete_map=habitat_color_map(),
        text_auto=".1%",
        title="Conservation-weighted observation mix",
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Which species define each habitat?")
species_rank = (
    filtered_obs.groupby(["habitat_type", "common_name"])["observation_id"]
    .count()
    .reset_index(name="observations")
)
species_rank["habitat_total"] = species_rank.groupby("habitat_type")["observations"].transform("sum")
species_rank["share_of_habitat"] = species_rank["observations"] / species_rank["habitat_total"]
species_rank = species_rank.sort_values(
    ["habitat_type", "share_of_habitat"],
    ascending=[True, False],
).groupby("habitat_type", group_keys=False).head(12)

left, right = st.columns([1.15, 1.05])
with left:
    fig = px.bar(
        species_rank,
        x="share_of_habitat",
        y="common_name",
        color="habitat_type",
        facet_col="habitat_type",
        facet_col_spacing=0.08,
        color_discrete_map=habitat_color_map(),
        title="Species that make up the largest share of each habitat's detections",
    )
    fig.update_xaxes(tickformat=".0%")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(styled_plotly(fig), use_container_width=True)

with right:
    habitat_pivot = (
        filtered_obs.pivot_table(
            index="common_name",
            columns="habitat_type",
            values="observation_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )
    habitat_columns = [col for col in habitat_pivot.columns if col != "common_name"]
    if len(habitat_columns) >= 2:
        primary, secondary = habitat_columns[:2]
        habitat_pivot["difference"] = habitat_pivot[primary] - habitat_pivot[secondary]
        habitat_pivot["dominant_habitat"] = habitat_pivot["difference"].apply(
            lambda value: primary if value >= 0 else secondary
        )
        habitat_pivot["absolute_gap"] = habitat_pivot["difference"].abs()
        standout = habitat_pivot.sort_values("absolute_gap", ascending=False).head(15)
        fig = px.bar(
            standout.sort_values("difference"),
            x="difference",
            y="common_name",
            color="dominant_habitat",
            color_discrete_map=habitat_color_map(),
            title=f"Largest separation between {primary} and {secondary}",
        )
        st.plotly_chart(styled_plotly(fig), use_container_width=True)

st.markdown("### Where does each habitat perform best?")
location_rank = (
    filtered_obs.groupby(["habitat_type", "admin_unit_code"])
    .agg(
        observations=("observation_id", "count"),
        species=("common_name", "nunique"),
        watchlist=("pif_watchlist_status", lambda s: s.fillna(False).sum()),
    )
    .reset_index()
)
location_rank["watchlist_share"] = location_rank.apply(
    lambda row: safe_pct(row["watchlist"], row["observations"]),
    axis=1,
)
fig = px.scatter(
    location_rank,
    x="observations",
    y="species",
    size="watchlist_share",
    color="habitat_type",
    hover_data=["admin_unit_code"],
    color_discrete_map=habitat_color_map(),
    title="Observation volume, species richness, and watchlist presence by park unit",
)
st.plotly_chart(styled_plotly(fig), use_container_width=True)

highlight_text(
    "Read this page as a habitat scorecard: one view for scale, one for species concentration, and one for where conservation-relevant detections cluster."
)
