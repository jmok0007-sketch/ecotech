"""Bulk-load disposal_locations.csv into ewaste_facilities.

Usage:
    python import_disposal.py
"""
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "seeds" / "disposal_locations.csv"


def main() -> int:
    df = pd.read_csv(DEFAULT_CSV)
    keep = ["facility_name", "address", "suburb", "postcode", "state",
            "latitude", "longitude", "coord_source"]
    df = df[keep].copy()
    df["postcode"] = df["postcode"].astype("Int64").astype(str).replace("<NA>", None)
    # `verified` column comes from a boolean signal — set True if coord_source
    # is from a primary geocoder rather than a postcode fallback.
    df["verified"] = df["coord_source"].fillna("").str.contains("maptiler").astype(bool)
    df = df.where(pd.notnull(df), None)
    print(f"Loaded {len(df)} rows from {DEFAULT_CSV}")

    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE ewaste_facilities RESTART IDENTITY")
            execute_values(
                cur,
                """
                INSERT INTO ewaste_facilities
                (facility_name, address, suburb, postcode, state,
                 latitude, longitude, coord_source, verified)
                VALUES %s
                """,
                df.itertuples(index=False, name=None),
                page_size=1000,
            )
        conn.commit()
        print(f"Inserted {len(df)} rows into ewaste_facilities")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
