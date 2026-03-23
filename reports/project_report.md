# Bird Species Observation Analysis Report

## Project Objective
Combine the forest and grassland monitoring workbooks into one cleaned dataset, compare bird activity across habitats, and surface patterns related to location, seasonality, and weather.

## Dataset Overview
- Total bird observations: 17,077
- Unique bird species: 126
- Total survey events: 1,408
- Forest sheets loaded: 11
- Grassland sheets loaded with data: 4

## Key Findings
- The habitat with the most recorded bird observations is **Forest** with 8,546 observations.
- Forest recorded 108 unique species, while Grassland recorded 107 unique species.
- The single busiest admin unit is **ANTI** (Grassland) with 3,588 observations.
- Temperature correlation with bird observations per survey event: -0.071.
- Humidity correlation with bird observations per survey event: -0.066.

## Most Observed Species
- Forest: Red-eyed Vireo (694), Carolina Wren (646), Northern Cardinal (595), Eastern Tufted Titmouse (541), Eastern Wood-Pewee (486)
- Grassland: Northern Cardinal (565), European Starling (516), Field Sparrow (506), Indigo Bunting (485), Grasshopper Sparrow (382)

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
