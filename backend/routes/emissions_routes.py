"""Heavy-metal emissions endpoints."""
from flask import Blueprint, request
from services import emissions_service
from utils.helpers import ok, fail

emissions_bp = Blueprint("emissions", __name__)


@emissions_bp.route("/state", methods=["GET"])
def by_state():
    try:
        data = emissions_service.list_by_state()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return fail(f"Database error: {e}", 503)


@emissions_bp.route("/facility", methods=["GET"])
def by_facility():
    """Get paginated facility emissions data (max 100 per page).

    Query parameters:
    - limit: rows per page (1-100, default 50)
    - page: page number (default 1)
    """
    try:
        limit = request.args.get("limit", default=50, type=int)
        page = request.args.get("page", default=1, type=int)

        # Validate page
        page = max(1, page)

        # Calculate offset from page number
        offset = (page - 1) * limit

        # Fetch paginated data
        result = emissions_service.list_by_facility(limit=limit, offset=offset)

        return ok(result['data'], meta={
            "count": len(result['data']),
            "pagination": result['pagination']
        })

    except Exception as e:
        return fail(f"Database error: {e}", 503)