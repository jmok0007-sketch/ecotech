"""Heavy-metal emissions endpoints."""
from flask import Blueprint
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
        data = emissions_service.list_by_facility()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return fail(f"Database error: {e}", 503)
