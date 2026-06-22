"""Profile raw mutual fund datasets and generate an ingestion summary report."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
SUMMARY_REPORT_PATH = REPORTS_DIR / "ingestion_summary.txt"


def profile_dataset(file_path: Path) -> Dict[str, object]:
    """Read a CSV file, print profiling details, and return summary metrics."""
    summary: Dict[str, object] = {
        "file_name": file_path.name,
        "status": "success",
        "shape": (0, 0),
        "missing_values": 0,
        "duplicate_count": 0,
        "invalid_datatypes": [],
        "error": "",
    }

    print(f"\nProcessing file: {file_path.name}")
    print("-" * 80)

    try:
        dataset = pd.read_csv(file_path)
        summary["shape"] = dataset.shape
        summary["missing_values"] = int(dataset.isnull().sum().sum())
        summary["duplicate_count"] = int(dataset.duplicated().sum())
        summary["invalid_datatypes"] = detect_invalid_datatypes(dataset)

        print(f"Shape: {dataset.shape}")
        print("\nData types:")
        print(dataset.dtypes)
        print("\nFirst 5 rows:")
        print(dataset.head())
        print("\nMissing value count by column:")
        print(dataset.isnull().sum())
        print(f"\nDuplicate row count: {summary['duplicate_count']}")

        if summary["invalid_datatypes"]:
            print(
                "\nPotential invalid datatype columns: "
                + ", ".join(summary["invalid_datatypes"])
            )
        else:
            print("\nPotential invalid datatype columns: None detected")

    except Exception as exc:  # pylint: disable=broad-except
        summary["status"] = "failed"
        summary["error"] = str(exc)
        print(f"Error while processing {file_path.name}: {exc}")

    return summary


def detect_invalid_datatypes(dataset: pd.DataFrame) -> List[str]:
    """Flag object columns that appear numeric but remain stored as text."""
    invalid_columns: List[str] = []

    for column in dataset.columns:
        if dataset[column].dtype != "object":
            continue

        cleaned_series = (
            dataset[column].dropna().astype(str).str.replace(",", "", regex=False)
        )
        if cleaned_series.empty:
            continue

        converted_values = pd.to_numeric(cleaned_series, errors="coerce")
        if converted_values.notna().mean() >= 0.8:
            invalid_columns.append(column)

    return invalid_columns


def generate_summary_report(dataset_summaries: List[Dict[str, object]]) -> None:
    """Write a consolidated ingestion summary report to the reports folder."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    total_datasets = len(dataset_summaries)
    successful_datasets = sum(
        1 for item in dataset_summaries if item["status"] == "success"
    )
    failed_datasets = total_datasets - successful_datasets
    total_missing_values = sum(
        int(item["missing_values"]) for item in dataset_summaries
    )
    total_duplicate_records = sum(
        int(item["duplicate_count"]) for item in dataset_summaries
    )

    lines = [
        "Mutual Fund Analytics - Data Ingestion Summary",
        "=" * 55,
        f"Total datasets scanned: {total_datasets}",
        f"Successful datasets: {successful_datasets}",
        f"Failed datasets: {failed_datasets}",
        f"Total missing values: {total_missing_values}",
        f"Total duplicate records: {total_duplicate_records}",
        "",
        "Dataset details:",
    ]

    for item in dataset_summaries:
        lines.extend(
            [
                "-" * 55,
                f"File name: {item['file_name']}",
                f"Status: {item['status']}",
                f"Shape: {item['shape']}",
                f"Missing values: {item['missing_values']}",
                f"Duplicate records: {item['duplicate_count']}",
                (
                    "Potential invalid datatypes: "
                    + (
                        ", ".join(item["invalid_datatypes"])
                        if item["invalid_datatypes"]
                        else "None"
                    )
                ),
                f"Error: {item['error'] or 'None'}",
            ]
        )

    SUMMARY_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSummary report generated at: {SUMMARY_REPORT_PATH}")


def ingest_all_csv_files() -> None:
    """Read and profile every CSV file available in the raw data directory."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {RAW_DATA_DIR}")
        generate_summary_report([])
        return

    dataset_summaries = [profile_dataset(file_path) for file_path in csv_files]
    generate_summary_report(dataset_summaries)


if __name__ == "__main__":
    ingest_all_csv_files()
