"""Validate that every amfi_code in fund_master exists in nav_history."""

from __future__ import annotations

from pathlib import Path
from typing import Set

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
FUND_MASTER_PATH = RAW_DATA_DIR / "01_fund_master.csv"
NAV_HISTORY_PATH = RAW_DATA_DIR / "02_nav_history.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "amfi_validation_report.txt"


def load_amfi_codes(file_path: Path, column: str = "amfi_code") -> Set[int]:
    """Load a CSV and return the set of unique values from the given column."""
    data = pd.read_csv(file_path, usecols=[column])
    return set(data[column].dropna().astype(int).unique())


def validate_amfi_codes() -> None:
    """Cross-check amfi_codes between fund_master and nav_history, write report."""
    master_codes = load_amfi_codes(FUND_MASTER_PATH)
    nav_codes = load_amfi_codes(NAV_HISTORY_PATH)

    missing_in_nav = sorted(master_codes - nav_codes)
    extra_in_nav = sorted(nav_codes - master_codes)
    matched = sorted(master_codes & nav_codes)

    # ---- Console output ----
    print(f"Total codes in fund_master  : {len(master_codes)}")
    print(f"Total codes in nav_history  : {len(nav_codes)}")
    print(f"Matched codes               : {len(matched)}")
    print(f"Missing in nav_history      : {len(missing_in_nav)}")
    print(f"Extra in nav_history        : {len(extra_in_nav)}")

    if missing_in_nav:
        print("\nCodes present in fund_master but MISSING in nav_history:")
        for code in missing_in_nav:
            print(f"  {code}")

    if extra_in_nav:
        print("\nCodes present in nav_history but NOT in fund_master:")
        for code in extra_in_nav:
            print(f"  {code}")

    # ---- Report file ----
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "AMFI Code Validation Report",
        "=" * 50,
        f"Total codes in fund_master  : {len(master_codes)}",
        f"Total codes in nav_history  : {len(nav_codes)}",
        f"Matched codes               : {len(matched)}",
        f"Missing in nav_history      : {len(missing_in_nav)}",
        f"Extra in nav_history        : {len(extra_in_nav)}",
        "",
        "Matched codes:",
    ]
    lines += [f"  {code}" for code in matched]

    if missing_in_nav:
        lines += [
            "",
            "Codes in fund_master MISSING from nav_history:",
        ]
        lines += [f"  {code}" for code in missing_in_nav]

    if extra_in_nav:
        lines += [
            "",
            "Codes in nav_history NOT in fund_master:",
        ]
        lines += [f"  {code}" for code in extra_in_nav]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nValidation report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    validate_amfi_codes()
