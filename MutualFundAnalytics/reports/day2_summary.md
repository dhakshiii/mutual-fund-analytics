# Day 2 Summary — Bluestock Mutual Fund Analytics

---

## Data Cleaning (`data_cleaning.py`)

All three official Bluestock datasets were cleaned using pandas and saved to `data/processed/`.

### `02_nav_history.csv` -> `data/processed/nav_history.csv`

| Check | Result |
|---|---|
| Source rows | 46,000 |
| Date converted to datetime | Yes |
| Sorted by amfi_code + date | Yes |
| Duplicate rows removed | 0 |
| NAV forward-filled (missing) | 0 |
| NAV <= 0 removed | 0 |
| Cleaned rows saved | 46,000 |

### `08_investor_transactions.csv` -> `data/processed/investor_transactions.csv`

| Check | Result |
|---|---|
| Source rows | 32,778 |
| Dates converted to datetime | Yes |
| transaction_type standardised | Yes (SIP / Lumpsum / Redemption) |
| Invalid transaction_type dropped | 0 |
| Amount <= 0 dropped | 0 |
| Invalid KYC status dropped | 0 |
| Cleaned rows saved | 32,778 |

### `07_scheme_performance.csv` -> `data/processed/scheme_performance.csv`

| Check | Result |
|---|---|
| Source rows | 40 |
| Return columns coerced to numeric | Yes |
| Return anomalies flagged (>200% or <-100%) | 0 |
| Expense ratio out of range (0.1-2.5) flagged | 0 |
| `expense_ratio_valid` column added | Yes |
| Cleaned rows saved | 40 |

---

## SQLite Warehouse (`load_sqlite.py`)

- Database: `bluestock_mf.db`
- Engine: SQLAlchemy `create_engine()` with SQLite backend
- Schema: `sql/schema.sql`

### Tables and Row Counts

| Table | Rows | Source |
|---|---:|---|
| `dim_fund` | 40 | `01_fund_master.csv` |
| `dim_date` | 1,296 | Derived from NAV + transaction dates |
| `fact_nav` | 46,000 | `data/processed/nav_history.csv` |
| `fact_transactions` | 32,778 | `data/processed/investor_transactions.csv` |
| `fact_performance` | 40 | `data/processed/scheme_performance.csv` |
| `fact_aum` | 90 | `03_aum_by_fund_house.csv` |

---

## Schema Design (`sql/schema.sql`)

### Tables

| Table | Primary Key | Foreign Keys | Constraints |
|---|---|---|---|
| `dim_fund` | `fund_key` (AUTOINCREMENT) | None | `amfi_code` UNIQUE, `expense_ratio_pct` BETWEEN 0.1-2.5 |
| `dim_date` | `date_key` (YYYYMMDD) | None | `full_date` UNIQUE, range checks on all date parts |
| `fact_nav` | `nav_key` (AUTOINCREMENT) | `fund_key`, `date_key` | `nav > 0`, UNIQUE(fund_key, date_key) |
| `fact_transactions` | `transaction_key` (AUTOINCREMENT) | `fund_key`, `date_key` | `amount_inr > 0`, CHECK on transaction_type and kyc_status |
| `fact_performance` | `performance_key` (AUTOINCREMENT) | `fund_key` | `expense_ratio_pct` BETWEEN 0.1-2.5, UNIQUE(fund_key) |
| `fact_aum` | `aum_key` (AUTOINCREMENT) | None | `aum_lakh_crore > 0`, UNIQUE(fund_house, snapshot_date) |

### Indexes Created

- `idx_fact_nav_fund` — fact_nav(fund_key)
- `idx_fact_nav_date` — fact_nav(date_key)
- `idx_fact_txn_fund` — fact_transactions(fund_key)
- `idx_fact_txn_date` — fact_transactions(date_key)
- `idx_fact_txn_type` — fact_transactions(transaction_type)
- `idx_fact_aum_date` — fact_aum(snapshot_date)

---

## Analytical Queries (`sql/queries.sql`)

| # | Query | Description |
|---|---|---|
| 1 | Latest NAV per fund | Most recent NAV for every scheme |
| 2 | Top 10 by 1-year return | Best performing funds by trailing 1Y return |
| 3 | Monthly SIP trend | SIP count and inflow amount by month |
| 4 | AUM by fund house | Latest AUM snapshot per AMC |
| 5 | NAV growth % | First vs latest NAV growth per fund |
| 6 | Transactions by type and KYC | Count and amounts split by type and KYC status |
| 7 | State-wise investment | Total SIP + Lumpsum invested per state |
| 8 | Risk category analytics | Avg expense ratio, Sharpe, 3Y return per risk bucket |
| 9 | Year-on-year SIP growth | Annual SIP inflow with YoY % change |
| 10 | Best alpha funds | Top funds by Jensen's alpha vs benchmark |

---

## Documentation

- `reports/data_dictionary.md` — column definitions for all processed files and warehouse tables
- `reports/data_cleaning_report.txt` — row-level cleaning metrics per dataset
- `reports/amfi_validation_report.txt` — AMFI code cross-validation (40/40 matched)
