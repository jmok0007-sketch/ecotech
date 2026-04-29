"""Business logic for health data: query DB, return dict-shaped results."""
from db.connection import get_cursor
from db.queries import health_queries as q
from models.health_model import HealthRow


def list_all(year=None, sex=None, cancer_type=None) -> list[dict]:
    params = {
        "year": int(year) if year else None,
        "sex": sex or None,
        "cancer_type": cancer_type or None,
    }
    sql = q.SELECT_BY_FILTERS if any(params.values()) else q.SELECT_ALL
    with get_cursor() as (_, cur):
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [HealthRow.from_row(dict(r)).to_dict() for r in rows]


def list_filter_options() -> dict:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_DISTINCT_YEARS)
        years = [r["year"] for r in cur.fetchall()]
        cur.execute(q.SELECT_DISTINCT_SEX)
        sexes = [r["sex"] for r in cur.fetchall()]
        cur.execute(q.SELECT_DISTINCT_CANCERS)
        cancers = [r["cancer_type"] for r in cur.fetchall()]
    return {"years": years, "sexes": sexes, "cancer_types": cancers}
