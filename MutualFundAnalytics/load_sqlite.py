"""
Load all cleaned Bluestock datasets into bluestock_mf.db using SQLAlchemy.

Tables loaded:
    dim_fund          <- 01_fund_master.csv
    dim_date          <- derived from NAV + transaction dates
    fact_nav          <- data/processed/nav_history.csv
    fact_transactions <- data/processed/investor_transactions.csv
    fact_performance  <- data/processed/scheme_performance.csv
    fact_aum          <- 03_aum_by_fund_house.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import create_engine, text


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DB_PATH = PROJECT_ROOT / "bluestock_mf.db"
DB_URL = f"sqlite:///{DB_PATH}"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def get_engine():
    """Create and return a SQLAlchemy engine for bluestock_mf.db."""
    return create_engine(DB_URL, echo=False)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def apply_schema(engine) -> None:
    """Drop and recreate all tables using sql/schema.sql."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    # Use the raw DBAPI connection so executescript is available
    raw_conn = engine.raw_connection()
    try:
        raw_conn.executescript(schema_sql)
        raw_conn.commit()
    finally:
        raw_conn.close()


# ---------------------------------------------------------------------------
# Date dimension builder
# ---------------------------------------------------------------------------

def build_dim_date(nav_df: pd.DataFrame, txn_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a conformed date dimension from all NAV and transaction dates.

    Returns a DataFrame with columns:
        date_key, full_date, day_of_month, month_num,
        month_name, quarter_num, year_num
    """
    nav_dates = pd.to_datetime(nav_df["date"]).dt.date
    txn_dates = pd.to_datetime(txn_df["transaction_date"]).dt.date

    all_dates = pd.Series(
        sorted(set(nav_dates) | set(txn_dates))
    ).astype("datetime64[ns]")

    return pd.DataFrame({
        "date_key":     all_dates.dt.strftime("%Y%m%d").astype(int),
        "full_date":    all_dates.dt.strftime("%Y-%m-%d"),
        "day_of_month": all_dates.dt.day,
        "month_num":    all_dates.dt.month,
        "month_name":   all_dates.dt.strftime("%B"),
        "quarter_num":  all_dates.dt.quarter,
        "year_num":     all_dates.dt.year,
    })


# ---------------------------------------------------------------------------
# Individual loaders
# ---------------------------------------------------------------------------

def load_dim_fund(engine, fund_master: pd.DataFrame) -> int:
    """Insert fund master records into dim_fund."""
    cols = [
        "amfi_code", "scheme_name", "fund_house", "category",
        "sub_category", "plan", "benchmark", "risk_category",
        "sebi_category_code", "expense_ratio_pct", "exit_load_pct",
        "min_sip_amount", "min_lumpsum_amount", "fund_manager",
    ]
    df = fund_master[cols].copy()
    df.to_sql("dim_fund", engine, if_exists="append", index=False)
    return len(df)


def load_dim_date(engine, dim_date: pd.DataFrame) -> int:
    """Insert date dimension rows into dim_date."""
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    return len(dim_date)


def _amfi_to_fund_key(engine) -> Dict[int, int]:
    """Return mapping of amfi_code -> fund_key from dim_fund."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT fund_key, amfi_code FROM dim_fund")
        )
        return {int(row[1]): int(row[0]) for row in result}


def load_fact_nav(engine, nav_df: pd.DataFrame, key_map: Dict[int, int]) -> int:
    """Insert cleaned NAV rows into fact_nav."""
    df = nav_df.copy()
    df["fund_key"] = df["amfi_code"].astype(int).map(key_map)
    df["date_key"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d").astype(int)
    df = df[["fund_key", "date_key", "nav"]].dropna(subset=["fund_key"])
    df["fund_key"] = df["fund_key"].astype(int)
    df.to_sql("fact_nav", engine, if_exists="append", index=False)
    return len(df)


def load_fact_transactions(
    engine, txn_df: pd.DataFrame, key_map: Dict[int, int]
) -> int:
    """Insert cleaned investor transactions into fact_transactions."""
    df = txn_df.copy()
    df["fund_key"] = df["amfi_code"].astype(int).map(key_map)
    df["date_key"] = (
        pd.to_datetime(df["transaction_date"]).dt.strftime("%Y%m%d").astype(int)
    )
    cols = [
        "investor_id", "fund_key", "date_key", "transaction_type",
        "amount_inr", "state", "city", "city_tier", "age_group",
        "gender", "annual_income_lakh", "payment_mode", "kyc_status",
    ]
    df = df[cols].dropna(subset=["fund_key"])
    df["fund_key"] = df["fund_key"].astype(int)
    df.to_sql("fact_transactions", engine, if_exists="append", index=False)
    return len(df)


def load_fact_performance(
    engine, perf_df: pd.DataFrame, key_map: Dict[int, int]
) -> int:
    """Insert cleaned scheme performance into fact_performance."""
    df = perf_df.copy()
    df["fund_key"] = df["amfi_code"].astype(int).map(key_map)
    cols = [
        "fund_key", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "aum_crore", "expense_ratio_pct", "morningstar_rating",
        "risk_grade", "expense_ratio_valid",
    ]
    # expense_ratio_valid may not exist if cleaning was skipped
    if "expense_ratio_valid" not in df.columns:
        df["expense_ratio_valid"] = 1
    df = df[cols].dropna(subset=["fund_key"])
    df["fund_key"] = df["fund_key"].astype(int)
    df.to_sql("fact_performance", engine, if_exists="append", index=False)
    return len(df)


def load_fact_aum(engine, aum_raw: pd.DataFrame) -> int:
    """Insert AUM data into fact_aum."""
    df = aum_raw.copy()
    df = df.rename(columns={"date": "snapshot_date"})
    cols = ["fund_house", "snapshot_date", "aum_lakh_crore", "aum_crore", "num_schemes"]
    df = df[cols]
    df.to_sql("fact_aum", engine, if_exists="append", index=False)
    return len(df)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_counts(engine) -> Dict[str, int]:
    """Query and return row counts for every warehouse table."""
    tables = [
        "dim_fund", "dim_date",
        "fact_nav", "fact_transactions", "fact_performance", "fact_aum",
    ]
    counts: Dict[str, int] = {}
    with engine.connect() as conn:
        for tbl in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
            counts[tbl] = int(result.scalar())
    return counts


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(counts: Dict[str, int]) -> None:
    """Print a formatted loading summary with row counts."""
    print("\n" + "=" * 50)
    print("SQLite Load Summary")
    print(f"Database : {DB_PATH}")
    print("-" * 50)
    for table, count in counts.items():
        print(f"  {table:<22} {count:>8} rows")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Orchestrate full warehouse load pipeline."""
    # Read raw and processed sources
    fund_master = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    nav_df = pd.read_csv(PROCESSED_DIR / "nav_history.csv")
    txn_df = pd.read_csv(PROCESSED_DIR / "investor_transactions.csv")
    perf_df = pd.read_csv(PROCESSED_DIR / "scheme_performance.csv")
    aum_raw = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")

    engine = get_engine()

    # Apply schema (drops and recreates tables)
    apply_schema(engine)
    print("Schema applied.")

    # Load dimensions first
    n_fund = load_dim_fund(engine, fund_master)
    print(f"Loaded dim_fund        : {n_fund} rows")

    dim_date = build_dim_date(nav_df, txn_df)
    n_date = load_dim_date(engine, dim_date)
    print(f"Loaded dim_date        : {n_date} rows")

    # Build surrogate key map after dim_fund is loaded
    key_map = _amfi_to_fund_key(engine)

    # Load facts
    n_nav = load_fact_nav(engine, nav_df, key_map)
    print(f"Loaded fact_nav        : {n_nav} rows")

    n_txn = load_fact_transactions(engine, txn_df, key_map)
    print(f"Loaded fact_transactions: {n_txn} rows")

    n_perf = load_fact_performance(engine, perf_df, key_map)
    print(f"Loaded fact_performance : {n_perf} rows")

    n_aum = load_fact_aum(engine, aum_raw)
    print(f"Loaded fact_aum        : {n_aum} rows")

    # Verify
    counts = verify_counts(engine)
    print_summary(counts)


if __name__ == "__main__":
    main()
