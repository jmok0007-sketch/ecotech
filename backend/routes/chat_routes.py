"""AI Device Optimizer endpoint.

A lightweight, rule-based classifier returns explanation + tips. This avoids
needing a multi-GB LLM running on the EB instance. If you want to bolt on
a real model later, swap the body of `optimize_device` for a Bedrock or
external API call — the response shape stays the same.
"""
from flask import Blueprint, request
from utils.helpers import normalize_text, fail

chat_bp = Blueprint("chat", __name__)


DEVICE_TYPES = {
    "laptop": {"label": "Laptop"},
    "phone": {"label": "Phone"},
}

ISSUE_RULES = [
    ("battery_drain", ["battery", "drain", "charge", "power", "overheat", "hot"]),
    ("storage_full", ["storage", "space", "full", "memory", "files", "photos"]),
    ("slow_performance", ["slow", "lag", "freez", "stuck", "performance", "crash"]),
]

ISSUE_CONTENT = {
    "slow_performance": {
        "label": "Slow performance",
        "explanation": "Devices slow down when they're managing too many apps, low storage, or overdue updates.",
        "suggestions": {
            "laptop": [
                "Restart the laptop to clear temporary clutter.",
                "Close apps you aren't using.",
                "Move large files to cloud or an external drive.",
                "Install pending software updates.",
            ],
            "phone": [
                "Restart the phone.",
                "Close background apps.",
                "Delete unused apps and old media.",
                "Update the phone's software.",
            ],
        },
    },
    "battery_drain": {
        "label": "Battery drain",
        "explanation": "Battery wears faster from heat, high brightness, and apps that run in the background.",
        "suggestions": {
            "laptop": [
                "Lower screen brightness, enable battery saver.",
                "Quit power-hungry apps shown in task manager.",
                "Keep the laptop cool — heat shortens battery life.",
                "If the battery is old, consider a battery replacement, not a new laptop.",
            ],
            "phone": [
                "Lower brightness and shorten screen timeout.",
                "Close battery-heavy apps and turn off features you don't need.",
                "Avoid leaving the phone in hot places.",
                "If the battery is aging, replace just the battery.",
            ],
        },
    },
    "storage_full": {
        "label": "Storage full",
        "explanation": "Low storage stops updates, slows the system, and prevents new app installs.",
        "suggestions": {
            "laptop": [
                "Delete large unused files and duplicates.",
                "Move photos and videos to cloud or external drive.",
                "Empty the trash/recycle bin.",
                "Uninstall apps you no longer use.",
            ],
            "phone": [
                "Delete old photos, videos, and downloads.",
                "Clear cached data in chat apps.",
                "Use cloud backup to free local storage.",
                "Remove apps you rarely open.",
            ],
        },
    },
    "general": {
        "label": "General device care",
        "explanation": "Most everyday issues get better after a restart, an update, and a quick storage cleanup.",
        "suggestions": {
            "laptop": [
                "Restart the laptop.",
                "Install pending updates.",
                "Close unused apps and browser tabs.",
                "Back up files and clean up old storage.",
            ],
            "phone": [
                "Restart the phone.",
                "Install pending updates.",
                "Close unused apps.",
                "Back up photos and clean up storage.",
            ],
        },
    },
}


def classify(text: str) -> str:
    norm = normalize_text(text)
    for category, keywords in ISSUE_RULES:
        if any(k in norm for k in keywords):
            return category
    return "general"


@chat_bp.route("/device-optimizer", methods=["POST"])
def optimize_device():
    payload = request.get_json(silent=True) or {}
    device = normalize_text(payload.get("device_type", ""))
    if device not in DEVICE_TYPES:
        return fail("device_type must be 'phone' or 'laptop'", 400)

    issue_text = (payload.get("issue_text") or "").strip()
    if not issue_text:
        return fail("Please describe the issue.", 400)

    category = classify(issue_text)
    content = ISSUE_CONTENT[category]

    return {
        "device_type": device,
        "device_label": DEVICE_TYPES[device]["label"],
        "issue_category": category,
        "issue_label": content["label"],
        "issue_explanation": content["explanation"],
        "suggestions": content["suggestions"][device],
        "model": "rule-based-v1",
    }
