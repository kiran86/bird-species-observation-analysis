from __future__ import annotations

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import sqlite3


DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = BASE_DIR / "reports"

SOURCE_FILES = {
    "Forest": DATA_DIR / "Bird_Monitoring_Data_FOREST.XLSX",
    "Grassland": DATA_DIR / "Bird_Monitoring_Data_GRASSLAND.XLSX",
}

EXPECTED_COLUMNS = {
    "Admin_Unit_Code",
    "Sub_Unit_Code",
    "Site_Name",
    "Plot_Name",
    "Location_Type",
    "Year",
    "Date",
    "Start_Time",
    "End_Time",
    "Observer",
    "Visit",
    "Interval_Length",
    "ID_Method",
    "Distance",
    "Flyover_Observed",
    "Sex",
    "Common_Name",
    "Scientific_Name",
    "AcceptedTSN",
    "NPSTaxonCode",
    "TaxonCode",
    "AOU_Code",
    "PIF_Watchlist_Status",
    "Regional_Stewardship_Status",
    "Temperature",
    "Humidity",
    "Sky",
    "Wind",
    "Disturbance",
    "Previously_Obs",
    "Initial_Three_Min_Cnt",
}


def snake_case(name: str) -> str:
    return (
        name.strip()
        .replace("/", " ")
        .replace("-", " ")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "pct")
        .lower()
        .replace(" ", "_")
    )


def load_workbook(path: Path, habitat_type: str) -> pd.DataFrame:
    workbook = pd.ExcelFile(path)
    frames: list[pd.DataFrame] = []

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name)
        if df.empty:
            continue

        for missing_col in EXPECTED_COLUMNS.difference(df.columns):
            df[missing_col] = pd.NA

        df["Source_Sheet"] = sheet_name
        df["Habitat_Type"] = habitat_type
        df["Site_Name"] = df["Site_Name"].fillna(sheet_name)
        df["NPSTaxonCode"] = df["NPSTaxonCode"].combine_first(df["TaxonCode"])
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    return combined


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [snake_case(col) for col in df.columns]

    rename_map = {
        "npstaxoncode": "taxon_code",
        "habitat_type": "habitat_type",
    }
    df = df.rename(columns=rename_map)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["visit"] = pd.to_numeric(df["visit"], errors="coerce").astype("Int64")
    df["acceptedtsn"] = pd.to_numeric(df["acceptedtsn"], errors="coerce").astype("Int64")
    df["taxon_code"] = pd.to_numeric(df["taxon_code"], errors="coerce").astype("Int64")
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")

    bool_like_columns = [
        "flyover_observed",
        "pif_watchlist_status",
        "regional_stewardship_status",
        "previously_obs",
        "initial_three_min_cnt",
    ]
    for column in bool_like_columns:
        if column in df.columns:
            df[column] = df[column].astype("boolean")

    df["observation_month"] = df["date"].dt.month_name()
    df["observation_month_num"] = df["date"].dt.month
    df["observation_year_month"] = df["date"].dt.to_period("M").astype("string")
    df["start_hour"] = pd.to_datetime(
        df["start_time"].astype("string"),
        format="%H:%M:%S",
        errors="coerce",
    ).dt.hour
    df["survey_event_id"] = (
        df["habitat_type"].astype("string").fillna("Unknown")
        + "|"
        + df["admin_unit_code"].astype("string").fillna("Unknown")
        + "|"
        + df["plot_name"].astype("string").fillna("Unknown")
        + "|"
        + df["date"].astype("string").fillna("Unknown")
        + "|"
        + df["start_time"].astype("string").fillna("Unknown")
        + "|"
        + df["observer"].astype("string").fillna("Unknown")
        + "|"
        + df["visit"].astype("string").fillna("Unknown")
    )
    df.insert(0, "observation_id", range(1, len(df) + 1))

    return df.sort_values(
        ["habitat_type", "admin_unit_code", "date", "plot_name", "common_name"],
        ignore_index=True,
    )


def build_event_summary(df: pd.DataFrame) -> pd.DataFrame:
    event_summary = (
        df.groupby(
            [
                "survey_event_id",
                "habitat_type",
                "admin_unit_code",
                "plot_name",
                "date",
                "observer",
                "visit",
                "temperature",
                "humidity",
                "sky",
                "wind",
            ],
            dropna=False,
        )
        .agg(
            bird_observation_count=("observation_id", "count"),
            unique_species_count=("common_name", "nunique"),
        )
        .reset_index()
    )
    return event_summary


def save_tables(df: pd.DataFrame, event_summary: pd.DataFrame) -> None:
    habitat_summary = (
        df.groupby("habitat_type", dropna=False)
        .agg(
            total_observations=("observation_id", "count"),
            unique_species=("common_name", "nunique"),
            unique_locations=("admin_unit_code", "nunique"),
        )
        .reset_index()
        .sort_values("total_observations", ascending=False)
    )

    location_summary = (
        df.groupby(["habitat_type", "admin_unit_code"], dropna=False)
        .agg(
            total_observations=("observation_id", "count"),
            unique_species=("common_name", "nunique"),
            avg_temperature=("temperature", "mean"),
            avg_humidity=("humidity", "mean"),
        )
        .reset_index()
        .sort_values(["habitat_type", "total_observations"], ascending=[True, False])
    )

    species_summary = (
        df.groupby(["habitat_type", "common_name"], dropna=False)
        .agg(
            total_observations=("observation_id", "count"),
            locations_present=("admin_unit_code", "nunique"),
        )
        .reset_index()
        .sort_values(["habitat_type", "total_observations"], ascending=[True, False])
    )

    monthly_summary = (
        df.dropna(subset=["observation_year_month"])
        .groupby(["observation_year_month", "habitat_type"], dropna=False)
        .agg(total_observations=("observation_id", "count"))
        .reset_index()
        .sort_values("observation_year_month")
    )

    weather_summary = (
        event_summary.assign(
            temperature_band=pd.cut(
                event_summary["temperature"],
                bins=[-100, 10, 15, 20, 25, 30, 100],
                labels=["<=10C", "10-15C", "15-20C", "20-25C", "25-30C", "30C+"],
            )
        )
        .groupby(["habitat_type", "temperature_band"], dropna=False, observed=False)
        .agg(
            avg_bird_observations=("bird_observation_count", "mean"),
            avg_unique_species=("unique_species_count", "mean"),
            survey_events=("survey_event_id", "count"),
        )
        .reset_index()
    )

    df.to_csv(OUTPUT_DIR / "cleaned_bird_observations.csv", index=False)
    event_summary.to_csv(OUTPUT_DIR / "survey_event_summary.csv", index=False)
    habitat_summary.to_csv(OUTPUT_DIR / "habitat_summary.csv", index=False)
    location_summary.to_csv(OUTPUT_DIR / "location_summary.csv", index=False)
    species_summary.to_csv(OUTPUT_DIR / "species_summary.csv", index=False)
    monthly_summary.to_csv(OUTPUT_DIR / "monthly_summary.csv", index=False)
    weather_summary.to_csv(OUTPUT_DIR / "weather_summary.csv", index=False)

    with sqlite3.connect(OUTPUT_DIR / "bird_observations.db") as conn:
        df.to_sql("bird_observations", conn, if_exists="replace", index=False)
        event_summary.to_sql("survey_event_summary", conn, if_exists="replace", index=False)
        habitat_summary.to_sql("habitat_summary", conn, if_exists="replace", index=False)
        location_summary.to_sql("location_summary", conn, if_exists="replace", index=False)
        species_summary.to_sql("species_summary", conn, if_exists="replace", index=False)
        monthly_summary.to_sql("monthly_summary", conn, if_exists="replace", index=False)
        weather_summary.to_sql("weather_summary", conn, if_exists="replace", index=False)


def save_figures(df: pd.DataFrame, event_summary: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")

    habitat_counts = (
        df.groupby("habitat_type", dropna=False)["observation_id"]
        .count()
        .reset_index(name="total_observations")
    )
    plt.figure(figsize=(8, 5))
    sns.barplot(data=habitat_counts, x="habitat_type", y="total_observations", palette="Set2")
    plt.title("Bird Observations by Habitat")
    plt.xlabel("Habitat")
    plt.ylabel("Observations")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "habitat_observations.png", dpi=200)
    plt.close()

    top_species = (
        df.groupby(["habitat_type", "common_name"], dropna=False)["observation_id"]
        .count()
        .reset_index(name="total_observations")
        .sort_values("total_observations", ascending=False)
        .groupby("habitat_type", group_keys=False)
        .head(8)
    )
    plt.figure(figsize=(12, 7))
    sns.barplot(
        data=top_species,
        x="total_observations",
        y="common_name",
        hue="habitat_type",
        palette="Set2",
    )
    plt.title("Top Observed Species by Habitat")
    plt.xlabel("Observations")
    plt.ylabel("Species")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_species_by_habitat.png", dpi=200)
    plt.close()

    monthly = (
        df.dropna(subset=["observation_year_month"])
        .groupby(["observation_year_month", "habitat_type"], dropna=False)["observation_id"]
        .count()
        .reset_index(name="total_observations")
    )
    plt.figure(figsize=(10, 5))
    sns.lineplot(
        data=monthly,
        x="observation_year_month",
        y="total_observations",
        hue="habitat_type",
        marker="o",
        palette="Set2",
    )
    plt.xticks(rotation=45, ha="right")
    plt.title("Monthly Bird Observations")
    plt.xlabel("Year-Month")
    plt.ylabel("Observations")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "monthly_observations.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.scatterplot(
        data=event_summary,
        x="temperature",
        y="bird_observation_count",
        hue="habitat_type",
        palette="Set2",
        alpha=0.7,
    )
    plt.title("Temperature vs Bird Observations per Survey Event")
    plt.xlabel("Temperature (C)")
    plt.ylabel("Bird Observations")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "temperature_vs_bird_count.png", dpi=200)
    plt.close()


def build_report(df: pd.DataFrame, event_summary: pd.DataFrame) -> None:
    habitat_summary = pd.read_csv(OUTPUT_DIR / "habitat_summary.csv")
    location_summary = pd.read_csv(OUTPUT_DIR / "location_summary.csv")
    species_summary = pd.read_csv(OUTPUT_DIR / "species_summary.csv")

    forest_species = int(
        habitat_summary.loc[habitat_summary["habitat_type"] == "Forest", "unique_species"].iloc[0]
    )
    grassland_species = int(
        habitat_summary.loc[habitat_summary["habitat_type"] == "Grassland", "unique_species"].iloc[0]
    )
    busiest_habitat_row = habitat_summary.sort_values("total_observations", ascending=False).iloc[0]
    top_location_row = location_summary.sort_values("total_observations", ascending=False).iloc[0]
    top_species_rows = species_summary.groupby("habitat_type", group_keys=False).head(5)

    temp_corr = event_summary["temperature"].corr(event_summary["bird_observation_count"])
    humidity_corr = event_summary["humidity"].corr(event_summary["bird_observation_count"])

    metrics = {
        "total_observations": int(df["observation_id"].count()),
        "unique_species": int(df["common_name"].nunique()),
        "survey_events": int(event_summary["survey_event_id"].nunique()),
        "forest_species": forest_species,
        "grassland_species": grassland_species,
        "temperature_bird_count_correlation": None if pd.isna(temp_corr) else round(float(temp_corr), 3),
        "humidity_bird_count_correlation": None if pd.isna(humidity_corr) else round(float(humidity_corr), 3),
    }
    (OUTPUT_DIR / "summary_metrics.json").write_text(json.dumps(metrics, indent=2))

    top_species_lines = []
    for habitat in ["Forest", "Grassland"]:
        subset = top_species_rows[top_species_rows["habitat_type"] == habitat]
        entries = ", ".join(
            f"{row.common_name} ({int(row.total_observations)})" for row in subset.itertuples()
        )
        top_species_lines.append(f"- {habitat}: {entries}")

    report = f"""# Bird Species Observation Analysis Report

## Project Objective
Combine the forest and grassland monitoring workbooks into one cleaned dataset, compare bird activity across habitats, and surface patterns related to location, seasonality, and weather.

## Dataset Overview
- Total bird observations: {metrics["total_observations"]:,}
- Unique bird species: {metrics["unique_species"]:,}
- Total survey events: {metrics["survey_events"]:,}
- Forest sheets loaded: 11
- Grassland sheets loaded with data: {df.loc[df["habitat_type"] == "Grassland", "source_sheet"].nunique()}

## Key Findings
- The habitat with the most recorded bird observations is **{busiest_habitat_row.habitat_type}** with {int(busiest_habitat_row.total_observations):,} observations.
- Forest recorded {forest_species} unique species, while Grassland recorded {grassland_species} unique species.
- The single busiest admin unit is **{top_location_row.admin_unit_code}** ({top_location_row.habitat_type}) with {int(top_location_row.total_observations):,} observations.
- Temperature correlation with bird observations per survey event: {metrics["temperature_bird_count_correlation"]}.
- Humidity correlation with bird observations per survey event: {metrics["humidity_bird_count_correlation"]}.

## Most Observed Species
{chr(10).join(top_species_lines)}

## Deliverables Produced
- Cleaned CSV dataset in `outputs/cleaned_bird_observations.csv`
- SQLite database in `outputs/bird_observations.db`
- Summary tables in `outputs/*.csv`
- Charts in `outputs/figures/`
- SQL analysis file in `sql/analysis_queries.sql`
- Dashboard starter in `app/streamlit_app.py`

## Notes
- Several grassland sheets are empty and were skipped automatically during ingestion.
- The grassland workbook uses `TaxonCode` while the forest workbook uses `NPSTaxonCode`; both were standardized into `taxon_code`.
- Grassland does not include `Site_Name`, so the source sheet name is used as a fallback.
"""
    (REPORTS_DIR / "project_report.md").write_text(report)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)

    (BASE_DIR / ".matplotlib").mkdir(exist_ok=True)

    frames = [
        frame
        for habitat, path in SOURCE_FILES.items()
        for frame in [load_workbook(path, habitat)]
        if not frame.empty
    ]
    raw = pd.concat(frames, ignore_index=True)
    cleaned = clean_dataset(raw)
    event_summary = build_event_summary(cleaned)
    save_tables(cleaned, event_summary)
    save_figures(cleaned, event_summary)
    build_report(cleaned, event_summary)

    print(f"Saved cleaned dataset with {len(cleaned):,} observations to {OUTPUT_DIR}.")


if __name__ == "__main__":
    main()
