PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

CREATE TABLE dim_fund (
    fund_key INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code TEXT NOT NULL UNIQUE,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    risk_grade TEXT NOT NULL
);

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    day_of_month INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    month_num INTEGER NOT NULL CHECK (month_num BETWEEN 1 AND 12),
    month_name TEXT NOT NULL,
    quarter_num INTEGER NOT NULL CHECK (quarter_num BETWEEN 1 AND 4),
    year_num INTEGER NOT NULL CHECK (year_num BETWEEN 2000 AND 2100)
);

CREATE TABLE fact_nav (
    nav_key INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    nav REAL NOT NULL CHECK (nav > 0),
    UNIQUE (fund_key, date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);

CREATE TABLE fact_transactions (
    transaction_key INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL UNIQUE,
    investor_id TEXT NOT NULL,
    fund_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    transaction_type TEXT NOT NULL
        CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount REAL NOT NULL CHECK (amount > 0),
    state TEXT NOT NULL,
    kyc_status TEXT NOT NULL
        CHECK (kyc_status IN ('Verified', 'Pending', 'Rejected')),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);

CREATE TABLE fact_performance (
    performance_key INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key INTEGER NOT NULL,
    as_of_date_key INTEGER NOT NULL,
    return_1y REAL NOT NULL,
    return_3y REAL NOT NULL,
    return_5y REAL NOT NULL,
    expense_ratio REAL NOT NULL CHECK (expense_ratio BETWEEN 0.1 AND 2.5),
    UNIQUE (fund_key, as_of_date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (as_of_date_key) REFERENCES dim_date (date_key)
);

CREATE TABLE fact_aum (
    aum_key INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key INTEGER NOT NULL,
    as_of_date_key INTEGER NOT NULL,
    aum REAL NOT NULL CHECK (aum > 0),
    UNIQUE (fund_key, as_of_date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (as_of_date_key) REFERENCES dim_date (date_key)
);
