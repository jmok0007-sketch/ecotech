"""Business logic for disposal-location endpoints."""
from db.connection import get_cursor
from db.queries import disposal_queries as q
from models.disposal_model import DisposalLocationRow


def list_all() -> list[dict]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_ALL)
        rows = cur.fetchall()
    return [DisposalLocationRow.from_row(dict(r)).to_dict() for r in rows]


def list_by_postcode(postcode: str) -> list[dict]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_BY_POSTCODE, {"postcode": postcode})
        rows = cur.fetchall()
    return [DisposalLocationRow.from_row(dict(r)).to_dict() for r in rows]
