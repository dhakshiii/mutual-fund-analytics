# Day 2 Summary

## Data Cleaning Summary

- Cleaned 6 raw NAV datasets from `data/raw` and saved the outputs to `data/processed`.
- Total cleaned NAV rows loaded for analytics: `19,881`.
- One invalid NAV row (`NAV <= 0`) was removed from `icici_bluechip.csv`.
- No duplicate records were found in the six raw NAV files.
- No missing NAV values required forward filling in the current source files.
- Generated `reports/data_cleaning_report.txt` with file-level cleaning metrics.

## Synthetic Datasets Generated

| Dataset | Rows | Notes |
|---|---:|---|
| `fund_master.csv` | 6 | Scheme master with fund house, category, subcategory, risk grade |
| `scheme_performance.csv` | 6 | 1Y, 3Y, 5Y returns and validated expense ratios |
| `investor_transactions.csv` | 5,000 | Synthetic investor transactions across SIP, Lumpsum, Redemption |
| `aum_data.csv` | 6 | Synthetic AUM snapshot values |

## SQLite Database Created

- Database file: `bluestock_mf.db`
- Schema file: `sql/schema.sql`
- Analytical query file: `sql/queries.sql`
- Loader script: `load_sqlite.py`

### Tables Created

- `dim_fund`
- `dim_date`
- `fact_nav`
- `fact_transactions`
- `fact_performance`
- `fact_aum`

### Verified Row Counts

| Table | Rows |
|---|---:|
| `dim_fund` | 6 |
| `dim_date` | 4,459 |
| `fact_nav` | 19,881 |
| `fact_transactions` | 5,000 |
| `fact_performance` | 6 |
| `fact_aum` | 6 |

## Queries Created

- Added 10 analytical SQL queries covering AUM ranking, NAV trends, transaction trends, SIP growth, state-wise activity, low expense funds, top 1-year returns, investment totals, and redemption totals.

## Supporting Documentation

- Added `reports/data_dictionary.md` documenting processed datasets and warehouse tables.
- Added `reports/day2_summary.md` as the Day 2 delivery report.
