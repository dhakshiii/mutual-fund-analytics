"""
Clean official Bluestock datasets and save to data/processed/.

Datasets cleaned:
    02_nav_history.csv
    07_scheme_performance.csv
    08_investor_transactions.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
CLEANING_REPORT = REPORTS_DIR / "data_cleaning_report.txt"

VALID_TRANSACTION_TYPES = {"SIP", "Lumpsum", "Redemption"}
VALID_KYC_STATUSES = {"Verified", "Pending", "Rejected"}
EXPENSE_RATIO_MIN = 0.1
EXPENSE_RATIO_MAX = 2.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dirs() -> None:
    """Create output directories if they do not exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _log(lines: List[str], message: str) -> None:
    """Append a message to the report lines list and print it."""
    print(message)
    lines.append(message)


# ---------------------------------------------------------------------------
# 02_nav_history.csv
# ---------------------------------------------------------------------------

def clean_nav_history(report: List[str]) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Clean 02_nav_history.csv.

    Steps:
        1. Convert date to datetime.
        2. Sort by amfi_code then date.
        3. Remove exact duplicate rows.
        4. Forward-fill missing NAV values within each fund.
        5. Drop rows where NAV <= 0.

    Returns:
        Tuple of (cleaned DataFrame, stats dict).
    """
    path = RAW_DIR / "02_nav_history.csv"
    df = pd.read_csv(path)
    stats: Dict[str, int] = {"source_rows": len(df)}

    _log(report, "\n--- 02_nav_history.csv ---")
    _log(report, f"  Source rows      : {stats['source_rows']}")

    # 1. Convert date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = df["date"].isna().sum()
    df = df.dropna(subset=["date"])
    stats["invalid_date_rows_dropped"] = int(invalid_dates)
    _log(report, f"  Invalid dates dropped : {invalid_dates}")

    # 2. Sort
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    # 3. Remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    stats["duplicates_removed"] = before - len(df)
    _log(report, f"  Duplicates removed : {stats['duplicates_removed']}")

    # 4. Forward-fill missing NAV per fund
    missing_before = df["nav"].isna().sum()
    df["nav"] = df.groupby("amfi_code")["nav"].transform(
        lambda s: s.ffill()
    )
    # Drop any remaining NaN (no prior value to fill from)
    df = df.dropna(subset=["nav"])
    stats["nav_forward_filled"] = int(missing_before)
    _log(report, f"  NAV forward-filled : {missing_before}")

    # 5. Remove NAV <= 0
    invalid_nav = (df["nav"] <= 0).sum()
    df = df[df["nav"] > 0]
    stats["invalid_nav_removed"] = int(invalid_nav)
    _log(report, f"  NAV <= 0 removed   : {invalid_nav}")

    # Ensure correct dtypes
    df["amfi_code"] = df["amfi_code"].astype(int)
    df["nav"] = df["nav"].astype(float)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    stats["cleaned_rows"] = len(df)
    _log(report, f"  Cleaned rows       : {stats['cleaned_rows']}")

    out = PROCESSED_DIR / "nav_history.csv"
    df.to_csv(out, index=False)
    _log(report, f"  Saved to           : {out}")

    return df, stats


# ---------------------------------------------------------------------------
# 08_investor_transactions.csv
# ---------------------------------------------------------------------------

def _standardize_transaction_type(val: str) -> str:
    """Normalise transaction_type to title case canonical form."""
    mapping = {
        "sip": "SIP",
        "lumpsum": "Lumpsum",
        "lump sum": "Lumpsum",
        "lump_sum": "Lumpsum",
        "redemption": "Redemption",
        "redeem": "Redemption",
    }
    return mapping.get(str(val).strip().lower(), str(val).strip())


def clean_investor_transactions(report: List[str]) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Clean 08_investor_transactions.csv.

    Steps:
        1. Convert transaction_date to datetime.
        2. Standardise transaction_type casing.
        3. Drop rows with unknown transaction_type.
        4. Validate amount > 0; drop invalid.
        5. Validate KYC status; drop invalid.

    Returns:
        Tuple of (cleaned DataFrame, stats dict).
    """
    path = RAW_DIR / "08_investor_transactions.csv"
    df = pd.read_csv(path)
    stats: Dict[str, int] = {"source_rows": len(df)}

    _log(report, "\n--- 08_investor_transactions.csv ---")
    _log(report, f"  Source rows      : {stats['source_rows']}")

    # 1. Convert dates
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    )
    invalid_dates = df["transaction_date"].isna().sum()
    df = df.dropna(subset=["transaction_date"])
    stats["invalid_date_rows_dropped"] = int(invalid_dates)
    _log(report, f"  Invalid dates dropped : {invalid_dates}")

    # 2. Standardise transaction_type
    df["transaction_type"] = df["transaction_type"].apply(
        _standardize_transaction_type
    )

    # 3. Drop unknown transaction types
    invalid_types = (~df["transaction_type"].isin(VALID_TRANSACTION_TYPES)).sum()
    df = df[df["transaction_type"].isin(VALID_TRANSACTION_TYPES)]
    stats["invalid_type_rows_dropped"] = int(invalid_types)
    _log(report, f"  Invalid transaction_type dropped : {invalid_types}")

    # 4. Validate amount > 0
    invalid_amt = (df["amount_inr"] <= 0).sum()
    df = df[df["amount_inr"] > 0]
    stats["invalid_amount_rows_dropped"] = int(invalid_amt)
    _log(report, f"  Amount <= 0 dropped : {invalid_amt}")

    # 5. Validate KYC status
    invalid_kyc = (~df["kyc_status"].isin(VALID_KYC_STATUSES)).sum()
    df = df[df["kyc_status"].isin(VALID_KYC_STATUSES)]
    stats["invalid_kyc_rows_dropped"] = int(invalid_kyc)
    _log(report, f"  Invalid KYC status dropped : {invalid_kyc}")

    # Final formatting
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    df["amfi_code"] = df["amfi_code"].astype(int)
    df["amount_inr"] = df["amount_inr"].astype(float)

    stats["cleaned_rows"] = len(df)
    _log(report, f"  Cleaned rows       : {stats['cleaned_rows']}")

    out = PROCESSED_DIR / "investor_transactions.csv"
    df.to_csv(out, index=False)
    _log(report, f"  Saved to           : {out}")

    return df, stats


# ---------------------------------------------------------------------------
# 07_scheme_performance.csv
# ---------------------------------------------------------------------------

def _flag_return_anomaly(series: pd.Series, label: str, report: List[str]) -> pd.Series:
    """
    Flag anomalous return values (>200% or <-100%) as NaN.

    Returns the cleaned series and logs anomaly count.
    """
    anomaly_mask = (series > 200) | (series < -100)
    count = int(anomaly_mask.sum())
    if count:
        _log(report, f"  Anomalous {label} values flagged NaN : {count}")
    series = series.where(~anomaly_mask, other=pd.NA)
    return series


def clean_scheme_performance(report: List[str]) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Clean 07_scheme_performance.csv.

    Steps:
        1. Coerce return columns to numeric.
        2. Flag return anomalies (>200% or <-100%) as NaN.
        3. Validate expense_ratio_pct is within 0.1 – 2.5.
           Rows outside range are flagged with a boolean column.

    Returns:
        Tuple of (cleaned DataFrame, stats dict).
    """
    path = RAW_DIR / "07_scheme_performance.csv"
    df = pd.read_csv(path)
    stats: Dict[str, int] = {"source_rows": len(df)}

    _log(report, "\n--- 07_scheme_performance.csv ---")
    _log(report, f"  Source rows      : {stats['source_rows']}")

    # 1. Coerce return columns to numeric
    return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                   "benchmark_3yr_pct", "alpha", "beta",
                   "sharpe_ratio", "sortino_ratio",
                   "std_dev_ann_pct", "max_drawdown_pct"]

    for col in return_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Flag return anomalies
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
        if col in df.columns:
            df[col] = _flag_return_anomaly(df[col], col, report)

    # 3. Validate expense_ratio_pct
    df["expense_ratio_pct"] = pd.to_numeric(
        df["expense_ratio_pct"], errors="coerce"
    )
    invalid_expense = (
        (df["expense_ratio_pct"] < EXPENSE_RATIO_MIN) |
        (df["expense_ratio_pct"] > EXPENSE_RATIO_MAX)
    ).sum()
    df["expense_ratio_valid"] = (
        df["expense_ratio_pct"].between(EXPENSE_RATIO_MIN, EXPENSE_RATIO_MAX)
    )
    stats["invalid_expense_ratio_flagged"] = int(invalid_expense)
    _log(report, f"  Expense ratio out of range (flagged) : {invalid_expense}")

    df["amfi_code"] = df["amfi_code"].astype(int)

    stats["cleaned_rows"] = len(df)
    _log(report, f"  Cleaned rows       : {stats['cleaned_rows']}")

    out = PROCESSED_DIR / "scheme_performance.csv"
    df.to_csv(out, index=False)
    _log(report, f"  Saved to           : {out}")

    return df, stats


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_cleaning_report(report: List[str]) -> None:
    """Write accumulated report lines to reports/data_cleaning_report.txt."""
    header = [
        "Mutual Fund Analytics - Data Cleaning Report",
        "=" * 55,
        "",
    ]
    CLEANING_REPORT.write_text(
        "\n".join(header + report), encoding="utf-8"
    )
    print(f"\nCleaning report saved -> {CLEANING_REPORT}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all cleaning steps and generate the cleaning report."""
    ensure_dirs()
    report: List[str] = []

    nav_df, nav_stats = clean_nav_history(report)
    txn_df, txn_stats = clean_investor_transactions(report)
    perf_df, perf_stats = clean_scheme_performance(report)

    # Summary
    report.append("\n" + "=" * 55)
    report.append("SUMMARY")
    report.append(f"  nav_history      : {nav_stats['cleaned_rows']} rows")
    report.append(f"  investor_txns    : {txn_stats['cleaned_rows']} rows")
    report.append(f"  scheme_perf      : {perf_stats['cleaned_rows']} rows")

    write_cleaning_report(report)

    print(f"\nAll cleaned files saved to: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
