"""Row mapper for the ewaste_facilities table."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DisposalLocationRow:
    facility_name: str
    address: Optional[str]
    suburb: Optional[str]
    postcode: Optional[str]
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    coord_source: Optional[str]
    verified: Optional[bool]

    @classmethod
    def from_row(cls, row: dict) -> "DisposalLocationRow":
        return cls(**{k: row.get(k) for k in cls.__annotations__})

    def to_dict(self) -> dict:
        return asdict(self)
