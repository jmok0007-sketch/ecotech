"""Business logic for emissions endpoints."""
from db.connection import get_cursor
from db.queries import emissions_queries as q
from models.emissions_model import EmissionStateRow, EmissionFacilityRow


def list_by_state() -> list[dict]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_BY_STATE)
        rows = cur.fetchall()
    return [EmissionStateRow.from_row(dict(r)).to_dict() for r in rows]


def list_by_facility(limit: int = 50, offset: int = 0) -> dict:
    """Fetch paginated facility emissions data.

    Args:
        limit: Number of rows to return (1-100, default 50)
        offset: Number of rows to skip (default 0)

    Returns:
        Dict with 'data' (list of facilities) and 'pagination' metadata
    """
    # Clamp limit to reasonable bounds
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    with get_cursor() as (_, cur):
        # Get total count
        cur.execute(q.COUNT_FACILITIES)
        total = cur.fetchone()['total']

        # Get paginated data
        cur.execute(q.SELECT_BY_FACILITY, (limit, offset))
        rows = cur.fetchall()

    data = [EmissionFacilityRow.from_row(dict(r)).to_dict() for r in rows]

    return {
        'data': data,
        'pagination': {
            'limit': limit,
            'offset': offset,
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'pages': (total + limit - 1) // limit if limit > 0 else 1
        }
    }
