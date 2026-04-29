"""Row mappers for emissions tables."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class EmissionStateRow:
    report_year: int
    state: str
    metal: str
    total_air_emission_kg: Optional[float]
    total_water_emission_kg: Optional[float]
    total_land_emission_kg: Optional[float]
    facility_count: Optional[int]

    @classmethod
    def from_row(cls, row: dict) -> "EmissionStateRow":
        return cls(**{k: row.get(k) for k in cls.__annotations__})

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EmissionFacilityRow:
    report_year: int
    facility_id: Optional[str]
    facility_name: Optional[str]
    state: Optional[str]
    postcode: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    metal: Optional[str]
    total_air_emission_kg: Optional[float]
    total_water_emission_kg: Optional[float]
    total_land_emission_kg: Optional[float]

    @classmethod
    def from_row(cls, row: dict) -> "EmissionFacilityRow":
        return cls(**{k: row.get(k) for k in cls.__annotations__})

    def to_dict(self) -> dict:
        return asdict(self)
