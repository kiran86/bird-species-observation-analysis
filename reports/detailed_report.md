# Bird Species Observation Analysis Report

## Executive Summary
This report combines forest and grassland monitoring data into a cleaned dataset and highlights major spatial, temporal, and environmental patterns in bird observations. Key outcomes include habitat-level comparison, monthly trends, species composition differences, and simple weather correlations. Visualizations listed below are the primary evidence supporting the findings.

## Project Objective
Combine the forest and grassland monitoring workbooks into one cleaned dataset, compare bird activity across habitats, and surface patterns related to location, seasonality, and weather.

## Dataset Overview
- Total bird observations: 17,077
- Unique bird species: 126
- Total survey events: 1,408
- Forest sheets loaded: 11
- Grassland sheets loaded with data: 4

## Major Visualizations (figures)
Below are the principal charts produced; open the images in `outputs/figures/` to inspect high-resolution versions.

- Figure 1 — Habitat observations comparison: Habitat-level totals and relative proportions. (outputs/figures/habitat_observations.png)

	![Figure 1 — Habitat observations comparison](../outputs/figures/habitat_observations.png)

	Interpretation: Forest accounts for the largest share of observations, driven by a combination of sampling effort and higher species richness in forested survey sheets.

- Figure 2 — Monthly observations trend: Seasonal activity and survey effort across months. (outputs/figures/monthly_observations.png)

	![Figure 2 — Monthly observations trend](../outputs/figures/monthly_observations.png)

	Interpretation: The time series highlights peak survey months and seasonality in detection rates. Use this to align future sampling or to control for effort in models.

- Figure 3 — Temperature vs. bird count per survey event: Simple scatter and LOESS fit. (outputs/figures/temperature_vs_bird_count.png)

	![Figure 3 — Temperature vs bird count](../outputs/figures/temperature_vs_bird_count.png)

	Interpretation: The analysis found a weak negative temperature correlation with counts (r ≈ -0.07). This suggests temperature alone is not a strong predictor of event-level counts but may interact with time-of-day or season.

- Figure 4 — Top species by habitat: Leading species composition for Forest vs. Grassland. (outputs/figures/top_species_by_habitat.png)

	![Figure 4 — Top species by habitat](../outputs/figures/top_species_by_habitat.png)

	Interpretation: While some species (e.g., Northern Cardinal) appear in both habitats, the relative rankings differ — useful for targeted conservation messaging.

## Key Findings (expanded)
- Habitat comparison: Forest recorded 8,546 observations and slightly higher unique-species richness (Forest: 108, Grassland: 107). See Figure 1 for counts and proportional breakdowns.
- Spatial hotspots: The single busiest administrative unit is **ANTI** (Grassland) with 3,588 observations — check `outputs/location_summary.csv` for per-location metrics.
- Seasonality: Monthly patterns show distinct peaks; adjust analyses for effort by including month or survey counts as covariates. See Figure 2.
- Weather correlations: Temperature correlation with bird observations per survey event: -0.071; humidity correlation: -0.066. These are small effects — consider multivariable models before inferring causality.
- Species-level insights: Top observed species per habitat are summarized in `outputs/species_summary.csv` and visualized in Figure 4.

## Summary Tables and Outputs
- Cleaned dataset: `outputs/cleaned_bird_observations.csv`
- Summary tables: `outputs/habitat_summary.csv`, `outputs/location_summary.csv`, `outputs/monthly_summary.csv`, `outputs/species_summary.csv`, `outputs/survey_event_summary.csv`
- Metrics JSON: `outputs/summary_metrics.json`
- Figures: `outputs/figures/` (see files listed at the repository root for exact names)

## Methods (short)
- Ingestion: Forest and grassland workbooks were parsed; empty sheets skipped.
- Standardization: `TaxonCode` and `NPSTaxonCode` were harmonized to `taxon_code`; `Site_Name` fallback applied where missing.
- Aggregation: Counts aggregated to survey-event, site, habitat, and month-level summaries.
- Visualizations: Plots produced using the cleaned dataset; figure files are in `outputs/figures/`.

## Recommendations and Next Steps
- Investigate effort bias: Normalize counts by survey effort or include effort covariates in models.
- Multivariable models: Fit GLMs or GAMs with habitat, month, temperature, humidity, and effort to isolate drivers of variation.
- Dashboard: Flesh out the `app` dashboard to include interactive filters for habitat, month, and species.
- Additional visuals to add: heatmaps of site-level richness, pairwise environmental variable panels, and model diagnostic plots.

## Reproducibility and How to Re-run
1. Ensure dependencies from `requirements.txt` are installed.
2. Run the data build script: `python src/build_dataset.py` to recreate `outputs/` files.
3. Re-generate figures by running the plotting functions in `app/dashboard_utils.py` or the notebook used for EDA.

## Appendix: Notes
- Several grassland sheets were empty and were skipped during ingestion.
- The grassland workbook uses `TaxonCode` while the forest workbook uses `NPSTaxonCode`; both were standardized into `taxon_code`.
- Grassland does not include `Site_Name`, so the source sheet name is used as a fallback.
