# Mutual Fund Analytics

## Project Overview

Mutual Fund Analytics is a Day 1 analytics project scaffold focused on
collecting mutual fund NAV history, storing raw datasets, and profiling
ingested CSV files for quality checks. The project provides a clean
foundation for later work such as SQL modeling, dashboarding, and
performance analytics.

## Folder Structure

```text
MutualFundAnalytics/
|
|-- data/
|   |-- raw/
|   `-- processed/
|
|-- notebooks/
|-- sql/
|-- dashboard/
|-- reports/
|
|-- data_ingestion.py
|-- live_nav_fetch.py
|-- requirements.txt
|-- README.md
`-- .gitignore
```

## Installation Steps

1. Create and activate a virtual environment.
2. Install project dependencies using `requirements.txt`.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running Instructions

1. Fetch NAV history from the API and save raw CSV files:

```bash
python live_nav_fetch.py
```

2. Profile all CSV files stored in `data/raw` and generate an ingestion
   summary report:

```bash
python data_ingestion.py
```

## API Source Information

- Source: `https://api.mfapi.in/mf/<scheme_code>`
- API Provider: `mfapi.in`
- Data captured: historical NAV series and scheme metadata

Configured scheme codes:

- HDFC Top 100 Direct: `125497`
- SBI Bluechip: `119551`
- ICICI Bluechip: `120503`
- Nippon Large Cap: `118632`
- Axis Bluechip: `119092`
- Kotak Bluechip: `120841`

## Deliverables

- Project-ready folder structure for analytics development
- `live_nav_fetch.py` for API extraction and CSV persistence
- `data_ingestion.py` for raw data profiling and summary generation
- `reports/data_quality_summary.txt` template for data quality reviews
- Dependency list and Git-ready project setup

## Git Commands

```bash
git init
git add .
git commit -m "Day 1: Data ingestion complete"
```
