"""Load processed mutual fund datasets into a SQLite star schema."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
DB_PATH = PROJECT_ROOT / "bluestock_mf.db"


def read_csv_rows(file_path: Path) -> list[dict[str, str]]:
    """Read CSV rows into a list of dictionaries."""
    with file_path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def list_clean_nav_files() -> list[Path]:
    """Return all cleaned NAV files in the processed folder."""
    return sorted(PROCESSED_DATA_DIR.glob("*_clean.csv"))


def build_date_dimension(
    nav_rows: list[dict[str, str]], transaction_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """Create a conformed date dimension from NAV and transaction dates."""
    all_dates = {
        row["date"] for row in nav_rows
    } | {row["transaction_date"] for row in transaction_rows}
    dimension_rows: list[dict[str, Any]] = []

    for date_text in sorted(all_dates):
        current_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        dimension_rows.append(
            {
                "date_key": int(current_date.strftime("%Y%m%d")),
                "full_date": current_date.isoformat(),
                "day_of_month": current_date.day,
                "month_num": current_date.month,
                "month_name": current_date.strftime("%B"),
                "quarter_num": ((current_date.month - 1) // 3) + 1,
                "year_num": current_date.year,
            }
        )

    return dimension_rows


def create_engine():
    """Create a SQLAlchemy engine when available."""
    try:
        from sqlalchemy import create_engine as sqlalchemy_create_engine
    except ImportError:
        return None

    return sqlalchemy_create_engine(f"sqlite:///{DB_PATH}")


def connect_database() -> tuple[Any, str]:
    """Prefer SQLAlchemy-backed raw connections, but allow sqlite3 fallback."""
    engine = create_engine()
    if engine is not None:
        return engine.raw_connection(), "sqlalchemy"
    return sqlite3.connect(DB_PATH), "sqlite3"


def execute_schema(connection: Any) -> None:
    """Apply the warehouse schema to the target SQLite database."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema_sql)


def insert_many(
    connection: Any, sql_statement: str, rows: list[tuple[Any, ...]]
) -> None:
    """Bulk insert rows with executemany."""
    if not rows:
        return
    connection.executemany(sql_statement, rows)


def build_fund_key_map(connection: Any) -> dict[str, int]:
    """Map natural scheme codes to surrogate fund keys."""
    cursor = connection.cursor()
    cursor.execute("SELECT fund_key, scheme_code FROM dim_fund")
    return {str(scheme_code): int(fund_key) for fund_key, scheme_code in cursor.fetchall()}


def load_dimensions_and_facts(connection: Any) -> dict[str, int]:
    """Load processed CSV datasets into the star schema."""
    fund_master_rows = read_csv_rows(PROCESSED_DATA_DIR / "fund_master.csv")
    performance_rows = read_csv_rows(PROCESSED_DATA_DIR / "scheme_performance.csv")
    transaction_rows = read_csv_rows(
        PROCESSED_DATA_DIR / "investor_transactions.csv"
    )
    aum_rows = read_csv_rows(PROCESSED_DATA_DIR / "aum_data.csv")

    nav_rows: list[dict[str, str]] = []
    for nav_file in list_clean_nav_files():
        nav_rows.extend(read_csv_rows(nav_file))

    date_rows = build_date_dimension(nav_rows, transaction_rows)
    latest_nav_date = max(row["date"] for row in nav_rows)
    snapshot_date_key = int(latest_nav_date.replace("-", ""))

    insert_many(
        connection,
        """
        INSERT INTO dim_fund (
            scheme_code, scheme_name, fund_house, category, subcategory, risk_grade
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["scheme_code"],
                row["scheme_name"],
                row["fund_house"],
                row["category"],
                row["subcategory"],
                row["risk_grade"],
            )
            for row in fund_master_rows
        ],
    )

    insert_many(
        connection,
        """
        INSERT INTO dim_date (
            date_key, full_date, day_of_month, month_num, month_name, quarter_num,
            year_num
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["date_key"],
                row["full_date"],
                row["day_of_month"],
                row["month_num"],
                row["month_name"],
                row["quarter_num"],
                row["year_num"],
            )
            for row in date_rows
        ],
    )

    fund_key_map = build_fund_key_map(connection)

    insert_many(
        connection,
        """
        INSERT INTO fact_nav (fund_key, date_key, nav)
        VALUES (?, ?, ?)
        """,
        [
            (
                fund_key_map[row["scheme_code"]],
                int(row["date"].replace("-", "")),
                float(row["nav"]),
            )
            for row in nav_rows
        ],
    )

    insert_many(
        connection,
        """
        INSERT INTO fact_transactions (
            transaction_id, investor_id, fund_key, date_key, transaction_type,
            amount, state, kyc_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["transaction_id"],
                row["investor_id"],
                fund_key_map[row["scheme_code"]],
                int(row["transaction_date"].replace("-", "")),
                row["transaction_type"],
                float(row["amount"]),
                row["state"],
                row["kyc_status"],
            )
            for row in transaction_rows
        ],
    )

    insert_many(
        connection,
        """
        INSERT INTO fact_performance (
            fund_key, as_of_date_key, return_1y, return_3y, return_5y, expense_ratio
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                fund_key_map[row["scheme_code"]],
                snapshot_date_key,
                float(row["return_1y"]),
                float(row["return_3y"]),
                float(row["return_5y"]),
                float(row["expense_ratio"]),
            )
            for row in performance_rows
        ],
    )

    insert_many(
        connection,
        """
        INSERT INTO fact_aum (fund_key, as_of_date_key, aum)
        VALUES (?, ?, ?)
        """,
        [
            (
                fund_key_map[row["scheme_code"]],
                snapshot_date_key,
                float(row["aum"]),
            )
            for row in aum_rows
        ],
    )

    return {
        "dim_fund": len(fund_master_rows),
        "dim_date": len(date_rows),
        "fact_nav": len(nav_rows),
        "fact_transactions": len(transaction_rows),
        "fact_performance": len(performance_rows),
        "fact_aum": len(aum_rows),
    }


def verify_row_counts(connection: Any) -> dict[str, int]:
    """Query row counts from every warehouse table."""
    table_names = [
        "dim_fund",
        "dim_date",
        "fact_nav",
        "fact_transactions",
        "fact_performance",
        "fact_aum",
    ]
    counts: dict[str, int] = {}
    cursor = connection.cursor()

    for table_name in table_names:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        counts[table_name] = int(cursor.fetchone()[0])

    return counts


def print_summary(connection_mode: str, load_counts: dict[str, int]) -> None:
    """Print the final load summary."""
    print(f"Database created at: {DB_PATH}")
    print(f"Connection mode: {connection_mode}")
    for table_name, row_count in load_counts.items():
        print(f"Loaded {table_name} = {row_count} rows")


def main() -> None:
    """Create the SQLite warehouse and load all processed datasets."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection, connection_mode = connect_database()
    try:
        execute_schema(connection)
        load_dimensions_and_facts(connection)
        connection.commit()
        counts = verify_row_counts(connection)
        print_summary(connection_mode, counts)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
