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
    try:
        limit = request.args.get("limit", default=50, type=int)

        if limit < 1:
            limit = 50

        if limit > 100:
            limit = 100

        data = emissions_service.list_by_facility()

        # Sort by lead value if available
        data = sorted(
            data,
            key=lambda x: float(
                x.get("lead") or
                x.get("lead_kg") or
                x.get("Lead") or
                0
            ),
            reverse=True
        )

        data = data[:limit]

        return ok(data, meta={
            "count": len(data),
            "limit": limit
        })

    except Exception as e:
        return fail(f"Database error: {e}", 503)