"""Fetch historical mutual fund NAV data and store it as CSV files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import requests


BASE_URL = "https://api.mfapi.in/mf"
RAW_DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"
REQUEST_TIMEOUT = 30

SCHEMES: Dict[str, int] = {
    "HDFC Top 100 Direct": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841,
}


def sanitize_filename(scheme_name: str) -> str:
    """Convert a scheme name into a filesystem-safe CSV filename."""
    safe_name = "".join(
        character.lower() if character.isalnum() else "_"
        for character in scheme_name.strip()
    )
    while "__" in safe_name:
        safe_name = safe_name.replace("__", "_")
    return safe_name.strip("_") + ".csv"


def validate_response(payload: dict, expected_code: int) -> bool:
    """Validate that the API payload contains expected metadata and NAV data."""
    meta = payload.get("meta", {})
    data = payload.get("data", [])

    if not meta or not isinstance(data, list) or not data:
        return False

    meta_code = str(meta.get("scheme_code", "")).strip()
    return meta_code == str(expected_code)


def fetch_nav(scheme_name: str, scheme_code: int) -> pd.DataFrame:
    """Fetch NAV history for a scheme and return a cleaned DataFrame."""
    response = requests.get(
        f"{BASE_URL}/{scheme_code}",
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "MutualFundAnalytics/1.0"},
    )
    response.raise_for_status()

    payload = response.json()
    if not validate_response(payload, scheme_code):
        raise ValueError(
            f"Unexpected API response for {scheme_name} ({scheme_code})."
        )

    nav_frame = pd.DataFrame(payload["data"])
    nav_frame["date"] = pd.to_datetime(
        nav_frame["date"], format="%d-%m-%Y", errors="coerce"
    )
    nav_frame["nav"] = pd.to_numeric(nav_frame["nav"], errors="coerce")
    nav_frame["scheme_name"] = scheme_name
    nav_frame["scheme_code"] = scheme_code

    ordered_columns = ["scheme_code", "scheme_name", "date", "nav"]
    remaining_columns = [
        column for column in nav_frame.columns if column not in ordered_columns
    ]
    return nav_frame[ordered_columns + remaining_columns].sort_values(
        by="date", ascending=True
    )


def save_csv(nav_frame: pd.DataFrame, scheme_name: str) -> Path:
    """Save NAV history to the raw data directory and return the output path."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DATA_DIR / sanitize_filename(scheme_name)
    nav_frame.to_csv(output_path, index=False)
    return output_path


def process_schemes(schemes: Dict[str, int]) -> List[dict]:
    """Fetch and save NAV data for each configured mutual fund scheme."""
    results: List[dict] = []

    for scheme_name, scheme_code in schemes.items():
        try:
            nav_frame = fetch_nav(scheme_name, scheme_code)
            output_path = save_csv(nav_frame, scheme_name)
            results.append(
                {
                    "scheme_name": scheme_name,
                    "scheme_code": scheme_code,
                    "status": "success",
                    "records_fetched": len(nav_frame),
                    "output_file": str(output_path),
                }
            )
            print(
                f"Saved {len(nav_frame)} NAV records for "
                f"{scheme_name} to {output_path}"
            )
        except (requests.RequestException, ValueError) as exc:
            results.append(
                {
                    "scheme_name": scheme_name,
                    "scheme_code": scheme_code,
                    "status": "failed",
                    "records_fetched": 0,
                    "output_file": "",
                    "error": str(exc),
                }
            )
            print(f"Failed to fetch {scheme_name} ({scheme_code}): {exc}")

    return results


def print_summary(results: Iterable[dict]) -> None:
    """Print a simple execution summary after NAV extraction."""
    successful_runs = 0
    failed_runs = 0

    for result in results:
        if result["status"] == "success":
            successful_runs += 1
        else:
            failed_runs += 1

    print("\nExecution summary")
    print("-" * 50)
    print(f"Successful schemes: {successful_runs}")
    print(f"Failed schemes: {failed_runs}")


if __name__ == "__main__":
    execution_results = process_schemes(SCHEMES)
    print_summary(execution_results)
