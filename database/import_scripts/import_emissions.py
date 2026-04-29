"""Bulk-load emissions seed CSVs into heavy_metal_state and heavy_metal_facility.

Usage:
    python import_emissions.py
"""
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

SEEDS = Path(__file__).resolve().parent.parent / "seeds"


def connect():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def clean_year(value):
    """
    Converts values like:
    1998       -> 1998
    1998/1999  -> 1998
    """
    if pd.isna(value):
        return None

    value = str(value).strip()

    if "/" in value:
        value = value.split("/")[0]

    return int(float(value))


def load_state(conn):
    df = pd.read_csv(SEEDS / "heavy_metal_state.csv")

    df = df[
        [
            "report_year",
            "state",
            "metal",
            "total_air_emission_kg",
            "total_water_emission_kg",
            "total_land_emission_kg",
            "facility_count",
        ]
    ]

    df["report_year"] = df["report_year"].apply(clean_year)

    df = df.where(pd.notnull(df), None)

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE heavy_metal_state RESTART IDENTITY")

        execute_values(
            cur,
            """
            INSERT INTO heavy_metal_state
            (report_year, state, metal,
             total_air_emission_kg, total_water_emission_kg, total_land_emission_kg,
             facility_count)
            VALUES %s
            """,
            df.itertuples(index=False, name=None),
            page_size=1000,
        )

    print(f"heavy_metal_state: {len(df)} rows")


def load_facility(conn):
    df = pd.read_csv(SEEDS / "heavy_metal_facility.csv")

    df = df[
        [
            "report_year",
            "facility_id",
            "facility_name",
            "state",
            "postcode",
            "latitude",
            "longitude",
            "metal",
            "total_air_emission_kg",
            "total_water_emission_kg",
            "total_land_emission_kg",
        ]
    ]

    df["report_year"] = df["report_year"].apply(clean_year)

    df["facility_id"] = df["facility_id"].astype(str)

    df["postcode"] = (
        df["postcode"]
        .astype("Int64")
        .astype(str)
        .replace("<NA>", None)
    )

    df = df.where(pd.notnull(df), None)

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE heavy_metal_facility RESTART IDENTITY")

        execute_values(
            cur,
            """
            INSERT INTO heavy_metal_facility
            (report_year, facility_id, facility_name, state, postcode,
             latitude, longitude, metal,
             total_air_emission_kg, total_water_emission_kg, total_land_emission_kg)
            VALUES %s
            """,
            df.itertuples(index=False, name=None),
            page_size=1000,
        )

    print(f"heavy_metal_facility: {len(df)} rows")


def main() -> int:
    conn = connect()

    try:
        load_state(conn)
        load_facility(conn)
        conn.commit()
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())