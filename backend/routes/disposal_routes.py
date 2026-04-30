"""E-waste disposal location endpoints."""
from flask import Blueprint, request
from services import disposal_service
from utils.helpers import ok, fail, parse_postcode

disposal_bp = Blueprint("disposal", __name__)


@disposal_bp.route("/disposal-locations", methods=["GET"])
def all_locations():
    """Get paginated disposal facility data (max 500 per page).

    Query parameters:
    - limit: rows per page (1-500, default 100)
    - page: page number (default 1)
    """
    try:
        # Get and validate parameters
        limit = request.args.get("limit", default=100, type=int)
        page = request.args.get("page", default=1, type=int)

        # Validate page (must be >= 1)
        if page < 1:
            page = 1

        # Validate limit (must be 1-500)
        if limit < 1 or limit > 500:
            limit = 100

        # Calculate offset from page number
        offset = (page - 1) * limit

        # Fetch paginated data
        result = disposal_service.list_all(limit=limit, offset=offset)

        return ok(result['data'], meta={
            "count": len(result['data']),
            "pagination": result['pagination']
        })

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        traceback.print_exc()
        return fail(f"Database error: {error_detail}", 503)


@disposal_bp.route("/disposal-locations/<postcode>", methods=["GET"])
def by_postcode(postcode):
    pc = parse_postcode(postcode)
    if not pc:
        return fail("Postcode must be 4 digits", 400)
    try:
        data = disposal_service.list_by_postcode(pc)
        return ok(data, meta={"count": len(data), "postcode": pc})
    except Exception as e:
        return fail(f"Database error: {e}", 503)
