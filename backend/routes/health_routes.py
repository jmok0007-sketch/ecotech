"""Health-data endpoints."""
from flask import Blueprint, request
from services import health_service
from utils.helpers import ok, fail

health_bp = Blueprint("health", __name__)


@health_bp.route("/all", methods=["GET"])
def get_all():
    try:
        data = health_service.list_all(
            year=request.args.get("year"),
            sex=request.args.get("sex"),
            cancer_type=request.args.get("cancer_type"),
        )
        return ok(data, meta={"count": len(data), "source": "postgresql"})
    except Exception as e:
        return fail(f"Database error: {e}", 503)


@health_bp.route("/filters", methods=["GET"])
def get_filters():
    try:
        data = health_service.list_filter_options()
        return ok(data)
    except Exception as e:
        return fail(f"Database error: {e}", 503)
