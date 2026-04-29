"""Plain-Python row-to-dict mappers for health data.

These exist so the API response shape is decoupled from raw DB columns.
If the DB schema ever changes, only the mapper changes — not the routes."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class HealthRow:
    year: int
    sex: Optional[str]
    cancer_type: Optional[str]
    cancer_cases: Optional[float]
    cancer_deaths: Optional[float]
    fatality_ratio: Optional[float]

    @classmethod
    def from_row(cls, row: dict) -> "HealthRow":
        return cls(
            year=row.get("year"),
            sex=row.get("sex"),
            cancer_type=row.get("cancer_type"),
            cancer_cases=row.get("cancer_cases"),
            cancer_deaths=row.get("cancer_deaths"),
            fatality_ratio=row.get("fatality_ratio"),
        )

    def to_dict(self) -> dict:
        return asdict(self)
