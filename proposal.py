"""
Proposal module for Industrial AI - Quotation Intelligence.
Saves quotation proposals as JSON files for persistence, comparison, and history display.
Proposals are the single source of truth for the Quotation screen and Compare feature.
"""

import os
import json
import logging
from datetime import datetime

import config

logger = logging.getLogger(__name__)

# Proposals directory (within quotations folder)
PROPOSALS_DIR = os.path.join(config.QUOTATION_DIR, "proposals")


def _ensure_dir():
    """Ensure proposals directory exists."""
    os.makedirs(PROPOSALS_DIR, exist_ok=True)


def save_proposal(quotation_data: dict) -> str:
    """
    Save a quotation proposal as a JSON file.

    Args:
        quotation_data: Complete quotation data dictionary

    Returns:
        Path to the saved proposal JSON file
    """
    _ensure_dir()
    quotation_number = quotation_data.get("quotation_number", "unknown")
    filename = f"{quotation_number}.json"
    filepath = os.path.join(PROPOSALS_DIR, filename)

    # Build proposal document
    proposal = {
        "quotation_number": quotation_number,
        "inventory_id": quotation_data.get("inventory_id"),
        "motor_details": quotation_data.get("motor_details", {}),
        "engineering_details": quotation_data.get("engineering_details", {}),
        "cost_breakdown": quotation_data.get("cost_breakdown", {}),
        "image_path": quotation_data.get("image_path"),
        "pdf_path": quotation_data.get("pdf_path"),
        "created_date": quotation_data.get("created_date", datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
        "status": "Generated",
        "saved_at": datetime.utcnow().isoformat(),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Saved proposal to %s", filepath)
    return filepath


def get_proposal(quotation_number: str) -> dict:
    """
    Load a proposal from file.

    Args:
        quotation_number: The quotation number to load

    Returns:
        Proposal dictionary or None
    """
    _ensure_dir()
    filepath = os.path.join(PROPOSALS_DIR, f"{quotation_number}.json")
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load proposal %s: %s", quotation_number, str(e))
        return None


def get_all_proposals() -> list:
    """
    Get all saved proposals (for history/quotation listing).

    Returns:
        List of proposal summary dicts, sorted by date descending
    """
    _ensure_dir()
    proposals = []

    for filename in os.listdir(PROPOSALS_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(PROPOSALS_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            motor = data.get("motor_details", {})
            cost = data.get("cost_breakdown", {})
            proposals.append({
                "quotation_number": data.get("quotation_number"),
                "inventory_id": data.get("inventory_id"),
                "manufacturer": motor.get("manufacturer"),
                "model": motor.get("model"),
                "grand_total": cost.get("grand_total", 0),
                "status": data.get("status", "Generated"),
                "pdf_path": data.get("pdf_path"),
                "proposal_path": filepath,
                "created_date": data.get("created_date", ""),
            })
        except Exception as e:
            logger.error("Error reading proposal %s: %s", filename, str(e))
            continue

    # Sort by created_date descending
    proposals.sort(key=lambda x: x.get("created_date", ""), reverse=True)
    return proposals


def delete_proposal(quotation_number: str) -> bool:
    """Delete a proposal file."""
    filepath = os.path.join(PROPOSALS_DIR, f"{quotation_number}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        logger.info("Deleted proposal %s", filepath)
        return True
    return False
