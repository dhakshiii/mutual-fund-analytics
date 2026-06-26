# Mutual Fund Analytics — Data Dictionary

Source datasets: Bluestock official datasets (`data/raw/`)

---

## Processed CSV Files (`data/processed/`)

### `nav_history.csv`
Source: `02_nav_history.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `amfi_code` | `INTEGER` | AMFI-assigned unique scheme identifier | `02_nav_history.csv` |
| `date` | `TEXT` (YYYY-MM-DD) | NAV observation date | `02_nav_history.csv` |
| `nav` | `REAL` | Net asset value per unit in INR | `02_nav_history.csv` |

### `investor_transactions.csv`
Source: `08_investor_transactions.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `investor_id` | `TEXT` | Unique investor identifier | `08_investor_transactions.csv` |
| `transaction_date` | `TEXT` (YYYY-MM-DD) | Date of transaction booking | `08_investor_transactions.csv` |
| `amfi_code` | `INTEGER` | AMFI scheme code for the invested fund | `08_investor_transactions.csv` |
| `transaction_type` | `TEXT` | One of: SIP, Lumpsum, Redemption | `08_investor_transactions.csv` |
| `amount_inr` | `REAL` | Transaction amount in Indian Rupees | `08_investor_transactions.csv` |
| `state` | `TEXT` | Investor state of residence | `08_investor_transactions.csv` |
| `city` | `TEXT` | Investor city of residence | `08_investor_transactions.csv` |
| `city_tier` | `TEXT` | City tier classification (Tier 1/2/3) | `08_investor_transactions.csv` |
| `age_group` | `TEXT` | Investor age band | `08_investor_transactions.csv` |
| `gender` | `TEXT` | Investor gender | `08_investor_transactions.csv` |
| `annual_income_lakh` | `REAL` | Investor annual income in lakhs INR | `08_investor_transactions.csv` |
| `payment_mode` | `TEXT` | Payment channel (UPI, Mandate, etc.) | `08_investor_transactions.csv` |
| `kyc_status` | `TEXT` | KYC status: Verified, Pending, Rejected | `08_investor_transactions.csv` |

### `scheme_performance.csv`
Source: `07_scheme_performance.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `amfi_code` | `INTEGER` | AMFI scheme identifier | `07_scheme_performance.csv` |
| `scheme_name` | `TEXT` | Mutual fund scheme display name | `07_scheme_performance.csv` |
| `fund_house` | `TEXT` | Asset management company name | `07_scheme_performance.csv` |
| `category` | `TEXT` | Broad asset class (Equity / Debt) | `07_scheme_performance.csv` |
| `plan` | `TEXT` | Plan type: Regular or Direct | `07_scheme_performance.csv` |
| `return_1yr_pct` | `REAL` | Trailing 1-year return percentage | `07_scheme_performance.csv` |
| `return_3yr_pct` | `REAL` | Trailing 3-year annualised return % | `07_scheme_performance.csv` |
| `return_5yr_pct` | `REAL` | Trailing 5-year annualised return % | `07_scheme_performance.csv` |
| `benchmark_3yr_pct` | `REAL` | Benchmark 3-year annualised return % | `07_scheme_performance.csv` |
| `alpha` | `REAL` | Jensen's alpha — excess return vs benchmark | `07_scheme_performance.csv` |
| `beta` | `REAL` | Portfolio sensitivity to market movements | `07_scheme_performance.csv` |
| `sharpe_ratio` | `REAL` | Risk-adjusted return (return per unit risk) | `07_scheme_performance.csv` |
| `sortino_ratio` | `REAL` | Downside risk-adjusted return | `07_scheme_performance.csv` |
| `std_dev_ann_pct` | `REAL` | Annualised standard deviation of returns | `07_scheme_performance.csv` |
| `max_drawdown_pct` | `REAL` | Maximum peak-to-trough decline % | `07_scheme_performance.csv` |
| `aum_crore` | `INTEGER` | Assets under management in INR crore | `07_scheme_performance.csv` |
| `expense_ratio_pct` | `REAL` | Annual total expense ratio % | `07_scheme_performance.csv` |
| `morningstar_rating` | `INTEGER` | Morningstar star rating (1-5) | `07_scheme_performance.csv` |
| `risk_grade` | `TEXT` | Risk classification label | `07_scheme_performance.csv` |
| `expense_ratio_valid` | `BOOLEAN` | True if expense_ratio_pct is within 0.1-2.5 | Derived during cleaning |

---

## SQLite Star Schema (`bluestock_mf.db`)

### `dim_fund`
Source: `01_fund_master.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `fund_key` | `INTEGER` | Surrogate primary key | Warehouse auto-generated |
| `amfi_code` | `INTEGER` | Natural AMFI scheme code (unique) | `01_fund_master.csv` |
| `scheme_name` | `TEXT` | Full scheme name | `01_fund_master.csv` |
| `fund_house` | `TEXT` | Asset management company | `01_fund_master.csv` |
| `category` | `TEXT` | Broad asset class | `01_fund_master.csv` |
| `sub_category` | `TEXT` | Product segment (Large Cap, Gilt, etc.) | `01_fund_master.csv` |
| `plan` | `TEXT` | Regular or Direct | `01_fund_master.csv` |
| `benchmark` | `TEXT` | Index used as performance benchmark | `01_fund_master.csv` |
| `risk_category` | `TEXT` | SEBI risk label | `01_fund_master.csv` |
| `sebi_category_code` | `TEXT` | SEBI product categorisation code | `01_fund_master.csv` |
| `expense_ratio_pct` | `REAL` | Annual expense ratio (0.1-2.5) | `01_fund_master.csv` |
| `exit_load_pct` | `REAL` | Exit load percentage | `01_fund_master.csv` |
| `min_sip_amount` | `INTEGER` | Minimum SIP amount in INR | `01_fund_master.csv` |
| `min_lumpsum_amount` | `INTEGER` | Minimum lump-sum amount in INR | `01_fund_master.csv` |
| `fund_manager` | `TEXT` | Name of the fund manager | `01_fund_master.csv` |

### `dim_date`
Derived from NAV and transaction dates.

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `date_key` | `INTEGER` | YYYYMMDD surrogate key | Derived |
| `full_date` | `TEXT` | ISO 8601 date string | Derived |
| `day_of_month` | `INTEGER` | Day number within month (1-31) | Derived |
| `month_num` | `INTEGER` | Month number (1-12) | Derived |
| `month_name` | `TEXT` | Full month name | Derived |
| `quarter_num` | `INTEGER` | Calendar quarter (1-4) | Derived |
| `year_num` | `INTEGER` | Calendar year | Derived |

### `fact_nav`
Source: `data/processed/nav_history.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `nav_key` | `INTEGER` | Surrogate primary key | Warehouse auto-generated |
| `fund_key` | `INTEGER` | FK to `dim_fund` | Derived during load |
| `date_key` | `INTEGER` | FK to `dim_date` (YYYYMMDD) | `nav_history.csv` |
| `nav` | `REAL` | Net asset value per unit; must be > 0 | `nav_history.csv` |

### `fact_transactions`
Source: `data/processed/investor_transactions.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `transaction_key` | `INTEGER` | Surrogate primary key | Warehouse auto-generated |
| `investor_id` | `TEXT` | Investor identifier | `investor_transactions.csv` |
| `fund_key` | `INTEGER` | FK to `dim_fund` | Derived during load |
| `date_key` | `INTEGER` | FK to `dim_date` (YYYYMMDD) | `investor_transactions.csv` |
| `transaction_type` | `TEXT` | SIP, Lumpsum, or Redemption | `investor_transactions.csv` |
| `amount_inr` | `REAL` | Transaction amount in INR; must be > 0 | `investor_transactions.csv` |
| `state` | `TEXT` | Investor state | `investor_transactions.csv` |
| `city` | `TEXT` | Investor city | `investor_transactions.csv` |
| `city_tier` | `TEXT` | City tier | `investor_transactions.csv` |
| `age_group` | `TEXT` | Investor age band | `investor_transactions.csv` |
| `gender` | `TEXT` | Investor gender | `investor_transactions.csv` |
| `annual_income_lakh` | `REAL` | Annual income in lakhs INR | `investor_transactions.csv` |
| `payment_mode` | `TEXT` | Payment channel | `investor_transactions.csv` |
| `kyc_status` | `TEXT` | Verified, Pending, or Rejected | `investor_transactions.csv` |

### `fact_performance`
Source: `data/processed/scheme_performance.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `performance_key` | `INTEGER` | Surrogate primary key | Warehouse auto-generated |
| `fund_key` | `INTEGER` | FK to `dim_fund` | Derived during load |
| `return_1yr_pct` | `REAL` | 1-year trailing return % | `scheme_performance.csv` |
| `return_3yr_pct` | `REAL` | 3-year trailing return % | `scheme_performance.csv` |
| `return_5yr_pct` | `REAL` | 5-year trailing return % | `scheme_performance.csv` |
| `benchmark_3yr_pct` | `REAL` | 3-year benchmark return % | `scheme_performance.csv` |
| `alpha` | `REAL` | Jensen's alpha | `scheme_performance.csv` |
| `beta` | `REAL` | Market sensitivity | `scheme_performance.csv` |
| `sharpe_ratio` | `REAL` | Risk-adjusted return | `scheme_performance.csv` |
| `sortino_ratio` | `REAL` | Downside risk-adjusted return | `scheme_performance.csv` |
| `std_dev_ann_pct` | `REAL` | Annualised standard deviation | `scheme_performance.csv` |
| `max_drawdown_pct` | `REAL` | Max peak-to-trough loss % | `scheme_performance.csv` |
| `aum_crore` | `INTEGER` | AUM in INR crore | `scheme_performance.csv` |
| `expense_ratio_pct` | `REAL` | Annual expense ratio (0.1-2.5) | `scheme_performance.csv` |
| `morningstar_rating` | `INTEGER` | Star rating 1-5 | `scheme_performance.csv` |
| `risk_grade` | `TEXT` | Risk classification | `scheme_performance.csv` |
| `expense_ratio_valid` | `INTEGER` | 1 = valid range, 0 = flagged | Derived during cleaning |

### `fact_aum`
Source: `03_aum_by_fund_house.csv`

| Column | Datatype | Definition | Source |
|---|---|---|---|
| `aum_key` | `INTEGER` | Surrogate primary key | Warehouse auto-generated |
| `fund_house` | `TEXT` | Asset management company name | `03_aum_by_fund_house.csv` |
| `snapshot_date` | `TEXT` (YYYY-MM-DD) | AUM reporting date (quarterly) | `03_aum_by_fund_house.csv` |
| `aum_lakh_crore` | `REAL` | AUM in lakh crore INR | `03_aum_by_fund_house.csv` |
| `aum_crore` | `INTEGER` | AUM in crore INR | `03_aum_by_fund_house.csv` |
| `num_schemes` | `INTEGER` | Number of active schemes | `03_aum_by_fund_house.csv` |
