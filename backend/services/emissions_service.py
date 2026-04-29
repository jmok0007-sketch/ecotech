"""Business logic for emissions endpoints."""
from db.connection import get_cursor
from db.queries import emissions_queries as q
from models.emissions_model import EmissionStateRow, EmissionFacilityRow


def list_by_state() -> list[dict]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_BY_STATE)
        rows = cur.fetchall()
    return [EmissionStateRow.from_row(dict(r)).to_dict() for r in rows]


def list_by_facility() -> list[dict]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_BY_FACILITY)
        rows = cur.fetchall()
    return [EmissionFacilityRow.from_row(dict(r)).to_dict() for r in rows]
