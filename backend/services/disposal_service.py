"""Business logic for disposal-location endpoints."""
from db.connection import get_cursor
from db.queries import disposal_queries as q
from models.disposal_model import DisposalLocationRow


def list_all(limit: int = 100, offset: int = 0) -> dict:
    """Fetch paginated disposal facilities data.

    Args:
        limit: Number of rows to return (1-500, default 100)
        offset: Number of rows to skip (default 0)

    Returns:
        Dict with 'data' (list of facilities) and 'pagination' metadata
    """
    # Clamp limit to reasonable bounds
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    with get_cursor() as (_, cur):
        # Get total count
        cur.execute(q.SELECT_ALL_COUNT)
        total = cur.fetchone()['total']

        # Get paginated data
        cur.execute(q.SELECT_ALL, (limit, offset))
        rows = cur.fetchall()

    data = [DisposalLocationRow.from_row(dict(r)).to_dict() for r in rows]

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


def list_by_postcode(postcode: str) -> list[dict]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_BY_POSTCODE, {"postcode": postcode})
        rows = cur.fetchall()
    return [DisposalLocationRow.from_row(dict(r)).to_dict() for r in rows]
