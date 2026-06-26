-- =============================================================
-- Bluestock Mutual Fund Analytics - Star Schema
-- Database: bluestock_mf.db (SQLite)
-- =============================================================

PRAGMA foreign_keys = ON;

-- Drop facts before dimensions (FK dependency order)
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

-- =============================================================
-- dim_fund  (source: 01_fund_master.csv)
-- =============================================================
CREATE TABLE dim_fund (
    fund_key            INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL UNIQUE,
    scheme_name         TEXT    NOT NULL,
    fund_house          TEXT    NOT NULL,
    category            TEXT    NOT NULL,
    sub_category        TEXT    NOT NULL,
    plan                TEXT    NOT NULL CHECK (plan IN ('Regular', 'Direct')),
    benchmark           TEXT,
    risk_category       TEXT    NOT NULL,
    sebi_category_code  TEXT    NOT NULL,
    expense_ratio_pct   REAL    NOT NULL CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    exit_load_pct       REAL    NOT NULL CHECK (exit_load_pct >= 0),
    min_sip_amount      INTEGER NOT NULL CHECK (min_sip_amount > 0),
    min_lumpsum_amount  INTEGER NOT NULL CHECK (min_lumpsum_amount > 0),
    fund_manager        TEXT
);

-- =============================================================
-- dim_date  (derived from NAV and transaction dates)
-- =============================================================
CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,       -- YYYYMMDD surrogate
    full_date    TEXT    NOT NULL UNIQUE,   -- ISO YYYY-MM-DD
    day_of_month INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    month_num    INTEGER NOT NULL CHECK (month_num BETWEEN 1 AND 12),
    month_name   TEXT    NOT NULL,
    quarter_num  INTEGER NOT NULL CHECK (quarter_num BETWEEN 1 AND 4),
    year_num     INTEGER NOT NULL CHECK (year_num BETWEEN 2000 AND 2100)
);

-- =============================================================
-- fact_nav  (source: 02_nav_history.csv)
-- =============================================================
CREATE TABLE fact_nav (
    nav_key  INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    nav      REAL    NOT NULL CHECK (nav > 0),
    UNIQUE (fund_key, date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);

-- =============================================================
-- fact_transactions  (source: 08_investor_transactions.csv)
-- =============================================================
CREATE TABLE fact_transactions (
    transaction_key  INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id      TEXT    NOT NULL,
    fund_key         INTEGER NOT NULL,
    date_key         INTEGER NOT NULL,
    transaction_type TEXT    NOT NULL
        CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr       REAL    NOT NULL CHECK (amount_inr > 0),
    state            TEXT,
    city             TEXT,
    city_tier        TEXT,
    age_group        TEXT,
    gender           TEXT,
    annual_income_lakh REAL,
    payment_mode     TEXT,
    kyc_status       TEXT    NOT NULL
        CHECK (kyc_status IN ('Verified', 'Pending', 'Rejected')),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);

-- =============================================================
-- fact_performance  (source: 07_scheme_performance.csv)
-- =============================================================
CREATE TABLE fact_performance (
    performance_key     INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key            INTEGER NOT NULL,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL    CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    morningstar_rating  INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade          TEXT,
    expense_ratio_valid INTEGER NOT NULL DEFAULT 1
        CHECK (expense_ratio_valid IN (0, 1)),
    UNIQUE (fund_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key)
);

-- =============================================================
-- fact_aum  (source: 03_aum_by_fund_house.csv)
-- Quarterly fund-house-level AUM; date_key not FK-constrained
-- because AUM snapshot dates differ from daily NAV dates.
-- =============================================================
CREATE TABLE fact_aum (
    aum_key        INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house     TEXT    NOT NULL,
    snapshot_date  TEXT    NOT NULL,   -- YYYY-MM-DD
    aum_lakh_crore REAL    NOT NULL CHECK (aum_lakh_crore > 0),
    aum_crore      INTEGER NOT NULL CHECK (aum_crore > 0),
    num_schemes    INTEGER NOT NULL CHECK (num_schemes > 0),
    UNIQUE (fund_house, snapshot_date)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fact_nav_fund    ON fact_nav (fund_key);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date    ON fact_nav (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_fund    ON fact_transactions (fund_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date    ON fact_transactions (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type    ON fact_transactions (transaction_type);
CREATE INDEX IF NOT EXISTS idx_fact_aum_date    ON fact_aum (snapshot_date);
