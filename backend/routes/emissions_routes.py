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
        # Get and validate parameters
        limit = request.args.get("limit", default=50, type=int)
        page = request.args.get("page", default=1, type=int)

        # Validate page (must be >= 1)
        if page < 1:
            page = 1

        # Validate limit (must be 1-100)
        if limit < 1 or limit > 100:
            limit = 50

        # Calculate offset from page number
        offset = (page - 1) * limit

        # Fetch paginated data
        result = emissions_service.list_by_facility(limit=limit, offset=offset)

        return ok(result['data'], meta={
            "count": len(result['data']),
            "pagination": result['pagination']
        })

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback.print_exc()
        return fail(f"Database error: {error_detail}", 503)