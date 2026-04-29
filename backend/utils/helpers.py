"""Small utilities reused across routes/services."""
import re
import math
from flask import jsonify


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def clean_value(value):
    """Convert NaN/invalid values to JSON-safe values"""
    if value is None:
        return None

    # Handle float NaN
    if isinstance(value, float) and math.isnan(value):
        return None

    # Handle string "NaN"
    if isinstance(value, str) and value.lower() == "nan":
        return None

    return value


def clean_data(data):
    """Clean list of dicts"""
    cleaned = []
    for row in data:
        cleaned.append({k: clean_value(v) for k, v in row.items()})
    return cleaned


def ok(data, meta: dict | None = None, status: int = 200):
    # 🔴 CLEAN DATA BEFORE RETURN
    cleaned_data = clean_data(data)

    body = {"items": cleaned_data}
    if meta:
        body["meta"] = meta

    return jsonify(body), status


def fail(detail: str, status: int = 400):
    return jsonify({"detail": detail}), status


def parse_postcode(value: str) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) == 4 else None