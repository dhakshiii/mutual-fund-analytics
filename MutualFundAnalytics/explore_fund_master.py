"""Explore and summarise the fund master dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


FUND_MASTER_PATH = (
    Path(__file__).resolve().parent / "data" / "raw" / "01_fund_master.csv"
)

# Columns that represent categorical dimensions of interest.
CATEGORY_COLUMNS = {
    "Unique fund houses": "fund_house",
    "Categories": "category",
    "Subcategories": "sub_category",
    "Risk categories": "risk_category",
    "SEBI category codes": "sebi_category_code",
}


def load_fund_master() -> pd.DataFrame:
    """Load the fund master CSV and return a DataFrame."""
    if not FUND_MASTER_PATH.exists():
        raise FileNotFoundError(f"Fund master file not found: {FUND_MASTER_PATH}")
    return pd.read_csv(FUND_MASTER_PATH)


def print_unique_values(data: pd.DataFrame) -> None:
    """Print unique values for each categorical dimension."""
    for label, column in CATEGORY_COLUMNS.items():
        if column not in data.columns:
            print(f"\n{label}: column '{column}' not found in dataset.")
            continue

        unique_vals = sorted(data[column].dropna().unique())
        print(f"\n{label} ({len(unique_vals)}):")
        for val in unique_vals:
            print(f"  - {val}")


def explore() -> None:
    """Load fund master data and print exploration summary."""
    data = load_fund_master()
    print(f"Fund master loaded: {data.shape[0]} rows, {data.shape[1]} columns\n")
    print_unique_values(data)


if __name__ == "__main__":
    explore()
