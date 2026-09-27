"""
Quotation module for Industrial AI - Quotation Intelligence.
Handles quotation generation and management.
"""

import os
import json
from datetime import datetime
from database import get_db_session, Inventory, Quotation, generate_quotation_number
from pricing import calculate_costs
from engineering import lookup_manufacturer, estimate_engineering


def generate_quotation(inventory_id: str, engineering_overrides: dict = None) -> dict:
    """
    Generate a complete quotation for an inventory item.

    Args:
        inventory_id: The inventory ID to generate quotation for
        engineering_overrides: Optional user-edited engineering values

    Returns:
        Dictionary with complete quotation data
    """
    db = get_db_session()
    try:
        # Get inventory record
        inventory = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
        if not inventory:
            raise ValueError(f"Inventory {inventory_id} not found")

        # Parse extracted data
        extracted_data = json.loads(inventory.extracted_data) if inventory.extracted_data else {}
        extracted_fields = extracted_data.get("extracted", extracted_data)

        # Get engineering data
        if inventory.engineering_data:
            engineering_data = json.loads(inventory.engineering_data)
        else:
            # Perform manufacturer lookup and estimation
            manufacturer = extracted_fields.get("manufacturer", "")
            power = extracted_fields.get("power") or extracted_fields.get("kva") or ""
            mfr_data = lookup_manufacturer(manufacturer, power)
            engineering_data = estimate_engineering(extracted_fields, mfr_data)

        # Apply user overrides if provided
        if engineering_overrides:
            for key, value in engineering_overrides.items():
                if value is not None and value != "":
                    engineering_data[key] = value

        # Calculate costs
        cost_breakdown = calculate_costs(engineering_data)

        # Generate quotation number
        quotation_number = generate_quotation_number(db)

        # Motor details for the quotation
        motor_details = {
            "manufacturer": extracted_fields.get("manufacturer"),
            "model": extracted_fields.get("model"),
            "equipment_type": extracted_fields.get("equipment_type"),
            "power": extracted_fields.get("power") or extracted_fields.get("kva"),
            "voltage": extracted_fields.get("voltage"),
            "current": extracted_fields.get("current") or extracted_fields.get("amps"),
            "rpm": extracted_fields.get("rpm"),
            "frequency": extracted_fields.get("frequency"),
            "phase": extracted_fields.get("phase"),
            "power_factor": extracted_fields.get("power_factor"),
            "frame_number": extracted_fields.get("frame_number"),
            "serial_number": extracted_fields.get("serial_number"),
            "duty": extracted_fields.get("duty"),
            "insulation_class": extracted_fields.get("insulation_class"),
            "connection": extracted_fields.get("connection"),
        }

        # Create quotation record
        quotation = Quotation(
            quotation_number=quotation_number,
            inventory_id=inventory_id,
            manufacturer=extracted_fields.get("manufacturer"),
            model=extracted_fields.get("model"),
            subtotal=cost_breakdown["subtotal"],
            gst_amount=cost_breakdown["gst_amount"],
            grand_total=cost_breakdown["grand_total"],
            cost_breakdown=json.dumps(cost_breakdown),
            engineering_details=json.dumps(engineering_data),
            motor_details=json.dumps(motor_details),
            status="Generated",
        )

        db.add(quotation)

        # Update inventory status
        inventory.status = "Quotation Generated"
        inventory.engineering_data = json.dumps(engineering_data)
        db.commit()

        return {
            "quotation_number": quotation_number,
            "inventory_id": inventory_id,
            "motor_details": motor_details,
            "engineering_details": engineering_data,
            "cost_breakdown": cost_breakdown,
            "image_path": inventory.image_path,
            "created_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        }

    finally:
        db.close()


def get_quotation(quotation_number: str) -> dict:
    """Get quotation details by quotation number."""
    db = get_db_session()
    try:
        quotation = (
            db.query(Quotation)
            .filter(Quotation.quotation_number == quotation_number)
            .first()
        )
        if not quotation:
            return None

        inventory = (
            db.query(Inventory)
            .filter(Inventory.inventory_id == quotation.inventory_id)
            .first()
        )

        return {
            "quotation_number": quotation.quotation_number,
            "inventory_id": quotation.inventory_id,
            "motor_details": json.loads(quotation.motor_details) if quotation.motor_details else {},
            "engineering_details": json.loads(quotation.engineering_details) if quotation.engineering_details else {},
            "cost_breakdown": json.loads(quotation.cost_breakdown) if quotation.cost_breakdown else {},
            "image_path": inventory.image_path if inventory else None,
            "pdf_path": quotation.pdf_path,
            "grand_total": quotation.grand_total,
            "status": quotation.status,
            "created_date": quotation.created_date.strftime("%Y-%m-%d %H:%M") if quotation.created_date else "",
        }
    finally:
        db.close()


def get_all_quotations() -> list:
    """Get all quotations for history page."""
    db = get_db_session()
    try:
        quotations = db.query(Quotation).order_by(Quotation.created_date.desc()).all()
        result = []
        for q in quotations:
            result.append({
                "quotation_number": q.quotation_number,
                "inventory_id": q.inventory_id,
                "manufacturer": q.manufacturer,
                "model": q.model,
                "grand_total": q.grand_total,
                "status": q.status,
                "pdf_path": q.pdf_path,
                "created_date": q.created_date.strftime("%Y-%m-%d %H:%M") if q.created_date else "",
            })
        return result
    finally:
        db.close()


def delete_quotation(quotation_number: str) -> bool:
    """Delete a quotation by quotation number."""
    db = get_db_session()
    try:
        quotation = (
            db.query(Quotation)
            .filter(Quotation.quotation_number == quotation_number)
            .first()
        )
        if not quotation:
            return False

        # Delete PDF file if exists
        if quotation.pdf_path and os.path.exists(quotation.pdf_path):
            os.remove(quotation.pdf_path)

        db.delete(quotation)
        db.commit()
        return True
    finally:
        db.close()
