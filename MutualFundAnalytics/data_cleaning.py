"""Clean NAV datasets and generate Day 2 processed business data."""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
CLEANING_REPORT_PATH = REPORTS_DIR / "data_cleaning_report.txt"

RAW_FILE_NAMES = [
    "axis_bluechip.csv",
    "hdfc_top_100_direct.csv",
    "icici_bluechip.csv",
    "kotak_bluechip.csv",
    "nippon_large_cap.csv",
    "sbi_bluechip.csv",
]

STATE_WEIGHTS = [
    ("Maharashtra", 0.18),
    ("Karnataka", 0.11),
    ("Delhi", 0.10),
    ("Tamil Nadu", 0.09),
    ("Gujarat", 0.08),
    ("Telangana", 0.08),
    ("West Bengal", 0.08),
    ("Uttar Pradesh", 0.10),
    ("Rajasthan", 0.06),
    ("Kerala", 0.05),
    ("Punjab", 0.04),
    ("Madhya Pradesh", 0.03),
]

TRANSACTION_TYPES = [
    ("SIP", 0.55),
    ("Lumpsum", 0.25),
    ("Redemption", 0.20),
]

KYC_STATUSES = [
    ("Verified", 0.82),
    ("Pending", 0.13),
    ("Rejected", 0.05),
]

FUND_METADATA = {
    "119092": {
        "scheme_name": "Axis Bluechip",
        "fund_house": "Axis Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap",
        "risk_grade": "Moderately High",
        "expense_ratio": 1.54,
        "aum": 34500.0,
    },
    "125497": {
        "scheme_name": "HDFC Top 100 Direct",
        "fund_house": "HDFC Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap",
        "risk_grade": "Moderately High",
        "expense_ratio": 1.08,
        "aum": 41800.0,
    },
    "120503": {
        "scheme_name": "ICICI Bluechip",
        "fund_house": "ICICI Prudential Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap",
        "risk_grade": "Moderately High",
        "expense_ratio": 1.22,
        "aum": 39250.0,
    },
    "120841": {
        "scheme_name": "Kotak Bluechip",
        "fund_house": "Kotak Mahindra Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap",
        "risk_grade": "Moderate",
        "expense_ratio": 1.14,
        "aum": 27640.0,
    },
    "118632": {
        "scheme_name": "Nippon Large Cap",
        "fund_house": "Nippon India Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap",
        "risk_grade": "Moderately High",
        "expense_ratio": 1.67,
        "aum": 25120.0,
    },
    "119551": {
        "scheme_name": "SBI Bluechip",
        "fund_house": "SBI Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap",
        "risk_grade": "Moderate",
        "expense_ratio": 0.94,
        "aum": 43780.0,
    },
}


@dataclass
class CleanedNavRow:
    """Represent one cleaned NAV observation."""

    scheme_code: str
    scheme_name: str
    nav_date: date
    nav: float


@dataclass
class CleaningStats:
    """Track per-file cleaning outcomes."""

    file_name: str
    source_rows: int = 0
    cleaned_rows: int = 0
    duplicates_removed: int = 0
    missing_values_handled: int = 0
    invalid_nav_rows_removed: int = 0
    datatype_errors: int = 0


def weighted_choice(options: list[tuple[str, float]], rng: random.Random) -> str:
    """Pick a value from weighted string options."""
    threshold = rng.random()
    cumulative = 0.0
    for label, weight in options:
        cumulative += weight
        if threshold <= cumulative:
            return label
    return options[-1][0]


def ensure_directories() -> None:
    """Create required output directories."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def read_raw_rows(file_path: Path, stats: CleaningStats) -> list[dict[str, object]]:
    """Read raw CSV rows and cast key fields into business-ready types."""
    parsed_rows: list[dict[str, object]] = []

    with file_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for raw_row in reader:
            stats.source_rows += 1
            try:
                scheme_code = str(raw_row["scheme_code"]).strip()
                scheme_name = str(raw_row["scheme_name"]).strip()
                nav_date = datetime.strptime(
                    str(raw_row["date"]).strip(), "%Y-%m-%d"
                ).date()

                nav_text = str(raw_row["nav"]).strip()
                nav_value = float(nav_text) if nav_text else None
            except (KeyError, TypeError, ValueError):
                stats.datatype_errors += 1
                continue

            parsed_rows.append(
                {
                    "scheme_code": scheme_code,
                    "scheme_name": scheme_name,
                    "date": nav_date,
                    "nav": nav_value,
                }
            )

    return parsed_rows


def deduplicate_rows(rows: Iterable[dict[str, object]], stats: CleaningStats) -> list[dict[str, object]]:
    """Remove duplicated scheme-date observations while preserving the first row."""
    unique_rows: list[dict[str, object]] = []
    seen_keys: set[tuple[str, date]] = set()

    for row in rows:
        row_key = (str(row["scheme_code"]), row["date"])
        if row_key in seen_keys:
            stats.duplicates_removed += 1
            continue
        seen_keys.add(row_key)
        unique_rows.append(row)

    return unique_rows


def remove_invalid_nav_rows(
    rows: Iterable[dict[str, object]], stats: CleaningStats
) -> list[dict[str, object]]:
    """Remove observations where NAV exists but is non-positive."""
    valid_rows: list[dict[str, object]] = []

    for row in rows:
        nav_value = row["nav"]
        if nav_value is not None and float(nav_value) <= 0:
            stats.invalid_nav_rows_removed += 1
            continue
        valid_rows.append(row)

    return valid_rows


def forward_fill_nav(rows: list[dict[str, object]], stats: CleaningStats) -> list[CleanedNavRow]:
    """Forward fill NAV values after sorting by scheme code and date."""
    last_nav_by_scheme: dict[str, float] = {}
    cleaned_rows: list[CleanedNavRow] = []

    for row in rows:
        scheme_code = str(row["scheme_code"])
        nav_value = row["nav"]

        if nav_value is None:
            if scheme_code not in last_nav_by_scheme:
                continue
            nav_value = last_nav_by_scheme[scheme_code]
            stats.missing_values_handled += 1
        else:
            nav_value = float(nav_value)

        last_nav_by_scheme[scheme_code] = nav_value
        cleaned_rows.append(
            CleanedNavRow(
                scheme_code=scheme_code,
                scheme_name=str(row["scheme_name"]),
                nav_date=row["date"],
                nav=nav_value,
            )
        )

    return cleaned_rows


def validate_cleaned_rows(rows: Iterable[CleanedNavRow]) -> None:
    """Validate cleaned data types before persisting."""
    for row in rows:
        if not isinstance(row.scheme_code, str):
            raise TypeError("scheme_code must be a string")
        if not isinstance(row.scheme_name, str):
            raise TypeError("scheme_name must be a string")
        if not isinstance(row.nav_date, date):
            raise TypeError("date must be a date instance")
        if not isinstance(row.nav, float):
            raise TypeError("nav must be a float")


def write_cleaned_csv(output_path: Path, rows: list[CleanedNavRow]) -> None:
    """Write cleaned NAV rows to a processed CSV."""
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["scheme_code", "scheme_name", "date", "nav"])
        for row in rows:
            writer.writerow(
                [
                    row.scheme_code,
                    row.scheme_name,
                    row.nav_date.isoformat(),
                    f"{row.nav:.4f}",
                ]
            )


def clean_nav_file(file_path: Path) -> tuple[list[CleanedNavRow], CleaningStats]:
    """Clean one raw NAV file and save the processed result."""
    stats = CleaningStats(file_name=file_path.name)
    parsed_rows = read_raw_rows(file_path, stats)
    parsed_rows.sort(key=lambda row: (str(row["scheme_code"]), row["date"]))
    unique_rows = deduplicate_rows(parsed_rows, stats)
    valid_rows = remove_invalid_nav_rows(unique_rows, stats)
    cleaned_rows = forward_fill_nav(valid_rows, stats)
    validate_cleaned_rows(cleaned_rows)

    output_name = file_path.stem + "_clean.csv"
    output_path = PROCESSED_DATA_DIR / output_name
    write_cleaned_csv(output_path, cleaned_rows)

    stats.cleaned_rows = len(cleaned_rows)
    return cleaned_rows, stats


def write_cleaning_report(stats_list: list[CleaningStats]) -> None:
    """Write the Day 2 data cleaning report."""
    lines = [
        "Mutual Fund Analytics - Data Cleaning Report",
        "=" * 50,
        f"Files processed: {len(stats_list)}",
        "",
    ]

    for stats in stats_list:
        lines.extend(
            [
                f"File name: {stats.file_name}",
                f"Source rows: {stats.source_rows}",
                f"Cleaned rows: {stats.cleaned_rows}",
                f"Duplicates removed: {stats.duplicates_removed}",
                f"Missing values handled: {stats.missing_values_handled}",
                f"Invalid NAV rows removed: {stats.invalid_nav_rows_removed}",
                f"Datatype errors skipped: {stats.datatype_errors}",
                "-" * 50,
            ]
        )

    CLEANING_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def trailing_return(nav_rows: list[CleanedNavRow], years: int) -> float:
    """Calculate a trailing CAGR-like return from available NAV history."""
    latest_row = nav_rows[-1]
    target_date = latest_row.nav_date - timedelta(days=365 * years)
    eligible_rows = [row for row in nav_rows if row.nav_date <= target_date]

    if not eligible_rows:
        return 0.0

    base_row = eligible_rows[-1]
    if base_row.nav <= 0:
        return 0.0

    year_span = max((latest_row.nav_date - base_row.nav_date).days / 365.25, 1)
    cagr = ((latest_row.nav / base_row.nav) ** (1 / year_span) - 1) * 100
    return round(cagr, 2)


def write_csv(output_path: Path, header: list[str], rows: Iterable[list[object]]) -> None:
    """Write generic CSV rows to disk."""
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerows(rows)


def generate_fund_master(scheme_codes: list[str]) -> int:
    """Create the fund master dataset."""
    output_path = PROCESSED_DATA_DIR / "fund_master.csv"
    rows = []

    for scheme_code in scheme_codes:
        metadata = FUND_METADATA[scheme_code]
        rows.append(
            [
                scheme_code,
                metadata["scheme_name"],
                metadata["fund_house"],
                metadata["category"],
                metadata["subcategory"],
                metadata["risk_grade"],
            ]
        )

    write_csv(
        output_path,
        [
            "scheme_code",
            "scheme_name",
            "fund_house",
            "category",
            "subcategory",
            "risk_grade",
        ],
        rows,
    )
    return len(rows)


def generate_scheme_performance(cleaned_data: dict[str, list[CleanedNavRow]]) -> int:
    """Create scheme performance metrics from cleaned NAV history."""
    output_path = PROCESSED_DATA_DIR / "scheme_performance.csv"
    rows = []

    for scheme_code, nav_rows in cleaned_data.items():
        metadata = FUND_METADATA[scheme_code]
        expense_ratio = float(metadata["expense_ratio"])
        if not 0.1 <= expense_ratio <= 2.5:
            raise ValueError(f"Expense ratio out of range for {scheme_code}")

        rows.append(
            [
                scheme_code,
                metadata["scheme_name"],
                f"{trailing_return(nav_rows, 1):.2f}",
                f"{trailing_return(nav_rows, 3):.2f}",
                f"{trailing_return(nav_rows, 5):.2f}",
                f"{expense_ratio:.2f}",
            ]
        )

    write_csv(
        output_path,
        [
            "scheme_code",
            "scheme_name",
            "return_1y",
            "return_3y",
            "return_5y",
            "expense_ratio",
        ],
        rows,
    )
    return len(rows)


def random_transaction_amount(transaction_type: str, rng: random.Random) -> float:
    """Generate a realistic transaction amount by transaction type."""
    if transaction_type == "SIP":
        amount = rng.randrange(500, 25001, 500)
    elif transaction_type == "Lumpsum":
        amount = rng.randrange(10000, 500001, 5000)
    else:
        amount = rng.randrange(1000, 300001, 1000)
    return float(amount)


def generate_investor_transactions(cleaned_data: dict[str, list[CleanedNavRow]]) -> int:
    """Create a synthetic investor transaction dataset."""
    output_path = PROCESSED_DATA_DIR / "investor_transactions.csv"
    rng = random.Random(20260624)
    scheme_codes = list(cleaned_data.keys())
    scheme_weights = []
    total_aum = sum(float(FUND_METADATA[code]["aum"]) for code in scheme_codes)

    for scheme_code in scheme_codes:
        scheme_weights.append(
            (scheme_code, float(FUND_METADATA[scheme_code]["aum"]) / total_aum)
        )

    investor_counter = 1500
    rows = []

    for sequence in range(1, 5001):
        scheme_code = weighted_choice(scheme_weights, rng)
        nav_rows = cleaned_data[scheme_code]
        min_date = nav_rows[0].nav_date
        max_date = nav_rows[-1].nav_date
        date_delta = max((max_date - min_date).days, 1)
        transaction_date = min_date + timedelta(days=rng.randint(0, date_delta))
        transaction_type = weighted_choice(TRANSACTION_TYPES, rng)
        amount = random_transaction_amount(transaction_type, rng)
        state = weighted_choice(STATE_WEIGHTS, rng)
        kyc_status = weighted_choice(KYC_STATUSES, rng)

        if rng.random() < 0.35:
            investor_counter += 1
        investor_id = f"INV{investor_counter:05d}"

        rows.append(
            [
                f"TXN{sequence:06d}",
                investor_id,
                scheme_code,
                transaction_date.isoformat(),
                transaction_type,
                f"{amount:.2f}",
                state,
                kyc_status,
            ]
        )

    write_csv(
        output_path,
        [
            "transaction_id",
            "investor_id",
            "scheme_code",
            "transaction_date",
            "transaction_type",
            "amount",
            "state",
            "kyc_status",
        ],
        rows,
    )
    return len(rows)


def generate_aum_data(scheme_codes: list[str]) -> int:
    """Create a synthetic AUM dataset."""
    output_path = PROCESSED_DATA_DIR / "aum_data.csv"
    rows = []

    for scheme_code in scheme_codes:
        metadata = FUND_METADATA[scheme_code]
        rows.append(
            [
                scheme_code,
                metadata["scheme_name"],
                f"{float(metadata['aum']):.2f}",
            ]
        )

    write_csv(output_path, ["scheme_code", "scheme_name", "aum"], rows)
    return len(rows)


def clean_all_nav_files() -> tuple[dict[str, list[CleanedNavRow]], list[CleaningStats]]:
    """Clean all required raw NAV files and return the in-memory result."""
    cleaned_data: dict[str, list[CleanedNavRow]] = {}
    stats_list: list[CleaningStats] = []

    for file_name in RAW_FILE_NAMES:
        file_path = RAW_DATA_DIR / file_name
        cleaned_rows, stats = clean_nav_file(file_path)
        stats_list.append(stats)

        if cleaned_rows:
            cleaned_data[cleaned_rows[0].scheme_code] = cleaned_rows

    return cleaned_data, stats_list


def main() -> None:
    """Execute Day 2 cleaning and processed dataset generation."""
    ensure_directories()
    cleaned_data, stats_list = clean_all_nav_files()
    write_cleaning_report(stats_list)

    scheme_codes = sorted(cleaned_data)
    fund_master_rows = generate_fund_master(scheme_codes)
    performance_rows = generate_scheme_performance(cleaned_data)
    transaction_rows = generate_investor_transactions(cleaned_data)
    aum_rows = generate_aum_data(scheme_codes)

    total_nav_rows = sum(len(rows) for rows in cleaned_data.values())
    print(f"Cleaned NAV files: {len(stats_list)}")
    print(f"Total cleaned NAV rows: {total_nav_rows}")
    print(f"Generated fund_master rows: {fund_master_rows}")
    print(f"Generated scheme_performance rows: {performance_rows}")
    print(f"Generated investor_transactions rows: {transaction_rows}")
    print(f"Generated aum_data rows: {aum_rows}")
    print(f"Cleaning report: {CLEANING_REPORT_PATH}")


if __name__ == "__main__":
    main()
