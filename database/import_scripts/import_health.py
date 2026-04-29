"""Bulk-load health_merged.csv into the health_merged table.

Usage:
    python import_health.py
    python import_health.py --csv ../seeds/health_merged.csv
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "seeds" / "health_merged.csv"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    df = df[["year", "sex", "cancer_type", "cancer_cases", "cancer_deaths", "fatality_ratio"]]
    df = df.where(pd.notnull(df), None)
    print(f"Loaded {len(df)} rows from {args.csv}")

    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE health_merged RESTART IDENTITY")
            execute_values(
                cur,
                """
                INSERT INTO health_merged
                (year, sex, cancer_type, cancer_cases, cancer_deaths, fatality_ratio)
                VALUES %s
                """,
                df.itertuples(index=False, name=None),
                page_size=1000,
            )
        conn.commit()
        print(f"Inserted {len(df)} rows into health_merged")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
