# Mutual Fund Analytics Data Dictionary

## Processed CSV Datasets

### `data/processed/*_clean.csv`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `scheme_code` | `TEXT` | Unique mutual fund scheme identifier from NAV source | `data/raw/*.csv` |
| `scheme_name` | `TEXT` | Mutual fund scheme display name | `data/raw/*.csv` |
| `date` | `DATE` (`YYYY-MM-DD`) | NAV observation date | `data/raw/*.csv` |
| `nav` | `REAL` | Cleaned net asset value per unit | `data/raw/*.csv` |

### `data/processed/fund_master.csv`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `scheme_code` | `TEXT` | Unique mutual fund scheme identifier | Cleaned NAV data |
| `scheme_name` | `TEXT` | Mutual fund scheme name | Cleaned NAV data |
| `fund_house` | `TEXT` | Asset management company managing the scheme | Synthetic business enrichment |
| `category` | `TEXT` | Broad investment classification | Synthetic business enrichment |
| `subcategory` | `TEXT` | Specific investment segment inside category | Synthetic business enrichment |
| `risk_grade` | `TEXT` | Investor-facing risk label | Synthetic business enrichment |

### `data/processed/scheme_performance.csv`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `scheme_code` | `TEXT` | Unique mutual fund scheme identifier | Cleaned NAV data |
| `scheme_name` | `TEXT` | Mutual fund scheme name | Cleaned NAV data |
| `return_1y` | `REAL` | Trailing 1-year annualized return percentage | Derived from cleaned NAV data |
| `return_3y` | `REAL` | Trailing 3-year annualized return percentage | Derived from cleaned NAV data |
| `return_5y` | `REAL` | Trailing 5-year annualized return percentage | Derived from cleaned NAV data |
| `expense_ratio` | `REAL` | Annual fund expense ratio percentage | Synthetic business enrichment |

### `data/processed/investor_transactions.csv`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `transaction_id` | `TEXT` | Unique transaction identifier | Synthetic transaction generation |
| `investor_id` | `TEXT` | Synthetic investor identifier | Synthetic transaction generation |
| `scheme_code` | `TEXT` | Invested mutual fund scheme | Synthetic transaction generation using cleaned NAV schemes |
| `transaction_date` | `DATE` (`YYYY-MM-DD`) | Investor transaction booking date | Synthetic transaction generation |
| `transaction_type` | `TEXT` | Transaction mode: SIP, Lumpsum, Redemption | Synthetic transaction generation |
| `amount` | `REAL` | Transaction amount in INR | Synthetic transaction generation |
| `state` | `TEXT` | Investor state / geography | Synthetic transaction generation |
| `kyc_status` | `TEXT` | Investor KYC review status | Synthetic transaction generation |

### `data/processed/aum_data.csv`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `scheme_code` | `TEXT` | Unique mutual fund scheme identifier | Cleaned NAV data |
| `scheme_name` | `TEXT` | Mutual fund scheme name | Cleaned NAV data |
| `aum` | `REAL` | Assets under management in INR crore | Synthetic business enrichment |

## SQLite Star Schema Tables

### `dim_fund`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `fund_key` | `INTEGER` | Surrogate key for fund dimension | SQLite warehouse |
| `scheme_code` | `TEXT` | Natural key for mutual fund scheme | `fund_master.csv` |
| `scheme_name` | `TEXT` | Mutual fund scheme name | `fund_master.csv` |
| `fund_house` | `TEXT` | Asset management company | `fund_master.csv` |
| `category` | `TEXT` | Broad investment classification | `fund_master.csv` |
| `subcategory` | `TEXT` | Product segment inside category | `fund_master.csv` |
| `risk_grade` | `TEXT` | Risk profile label | `fund_master.csv` |

### `dim_date`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `date_key` | `INTEGER` | Surrogate date key in `YYYYMMDD` format | Derived from NAV and transaction dates |
| `full_date` | `TEXT` | Calendar date in ISO format | Derived from NAV and transaction dates |
| `day_of_month` | `INTEGER` | Day number within month | Derived from `full_date` |
| `month_num` | `INTEGER` | Month number | Derived from `full_date` |
| `month_name` | `TEXT` | Month name | Derived from `full_date` |
| `quarter_num` | `INTEGER` | Quarter number | Derived from `full_date` |
| `year_num` | `INTEGER` | Calendar year | Derived from `full_date` |

### `fact_nav`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `nav_key` | `INTEGER` | Surrogate key for NAV fact row | SQLite warehouse |
| `fund_key` | `INTEGER` | Surrogate fund key linked to `dim_fund` | Derived during warehouse load |
| `date_key` | `INTEGER` | NAV observation date linked to `dim_date` | `*_clean.csv` |
| `nav` | `REAL` | Net asset value per unit | `*_clean.csv` |

### `fact_transactions`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `transaction_key` | `INTEGER` | Surrogate key for transaction fact row | SQLite warehouse |
| `transaction_id` | `TEXT` | Unique business transaction identifier | `investor_transactions.csv` |
| `investor_id` | `TEXT` | Synthetic investor identifier | `investor_transactions.csv` |
| `fund_key` | `INTEGER` | Surrogate fund key linked to `dim_fund` | Derived during warehouse load |
| `date_key` | `INTEGER` | Transaction date linked to `dim_date` | `investor_transactions.csv` |
| `transaction_type` | `TEXT` | SIP, Lumpsum, or Redemption | `investor_transactions.csv` |
| `amount` | `REAL` | Transaction amount in INR | `investor_transactions.csv` |
| `state` | `TEXT` | Investor state | `investor_transactions.csv` |
| `kyc_status` | `TEXT` | KYC verification outcome | `investor_transactions.csv` |

### `fact_performance`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `performance_key` | `INTEGER` | Surrogate key for performance fact row | SQLite warehouse |
| `fund_key` | `INTEGER` | Surrogate fund key linked to `dim_fund` | Derived during warehouse load |
| `as_of_date_key` | `INTEGER` | Snapshot date linked to `dim_date` | Derived from latest NAV date |
| `return_1y` | `REAL` | Trailing 1-year annualized return percentage | `scheme_performance.csv` |
| `return_3y` | `REAL` | Trailing 3-year annualized return percentage | `scheme_performance.csv` |
| `return_5y` | `REAL` | Trailing 5-year annualized return percentage | `scheme_performance.csv` |
| `expense_ratio` | `REAL` | Annual expense ratio percentage | `scheme_performance.csv` |

### `fact_aum`

| Column | Datatype | Business meaning | Source |
|---|---|---|---|
| `aum_key` | `INTEGER` | Surrogate key for AUM fact row | SQLite warehouse |
| `fund_key` | `INTEGER` | Surrogate fund key linked to `dim_fund` | Derived during warehouse load |
| `as_of_date_key` | `INTEGER` | Snapshot date linked to `dim_date` | Derived from latest NAV date |
| `aum` | `REAL` | Assets under management in INR crore | `aum_data.csv` |
