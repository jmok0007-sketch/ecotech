"""E-waste disposal location endpoints."""
from flask import Blueprint
from services import disposal_service
from utils.helpers import ok, fail, parse_postcode

disposal_bp = Blueprint("disposal", __name__)


@disposal_bp.route("/disposal-locations", methods=["GET"])
def all_locations():
    try:
        data = disposal_service.list_all()
        return ok(data, meta={"count": len(data)})
    except Exception as e:
        return fail(f"Database error: {e}", 503)


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
