# Bird Species Observation Analysis

This project combines bird monitoring observations from forest and grassland Excel workbooks into a single cleaned dataset for analysis, SQL exploration, and dashboarding.

## Project Flow

1. Read every worksheet from the forest and grassland Excel files.
2. Add location and habitat metadata.
3. Standardize the schema across both workbooks.
4. Clean and export a unified dataset.
5. Generate summary tables, charts, SQL-ready tables, and a report.
6. Use the outputs in Streamlit or Power BI.

## Repository Layout

- `data/`: source Excel workbooks
- `src/build_dataset.py`: ingestion, cleaning, export, and chart generation
- `outputs/`: cleaned dataset, summary tables, database, and figures
- `sql/analysis_queries.sql`: starter SQL answers to the business questions
- `app/streamlit_app.py`: dashboard home page
- `app/pages/`: focused Streamlit pages for habitat comparison, species exploration, and survey conditions
- `reports/project_report.md`: generated project report

## Setup

```bash
python3 -m pip install -r requirements.txt
python3 src/build_dataset.py
streamlit run app/streamlit_app.py
```

## Deliverables

- Cleaned dataset CSV
- SQLite database for SQL practice
- Summary CSV tables
- PNG charts
- SQL query file
- Markdown report
- Multipage Streamlit dashboard with filtered exploratory views
