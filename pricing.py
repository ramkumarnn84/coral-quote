"""
Pricing module for Industrial AI - Quotation Intelligence.
Contains editable pricing dictionary and cost calculation logic.
"""

# Default pricing dictionary (INR)
DEFAULT_PRICING = {
    "copper_per_kg": 1050.0,
    "oil_per_litre": 650.0,
    "nomex_insulation": 8500.0,
    "insulation_paper": 4500.0,
    "varnish": 5500.0,
    "labour_per_hour": 1200.0,
    "testing_charges": 3500.0,
    "painting_charges": 2500.0,
    "bearing_cost": 3000.0,
    "transport_charges": 2000.0,
    "miscellaneous": 1500.0,
    "gst_percentage": 18.0,
}

# In-memory pricing (can be updated via API)
current_pricing = DEFAULT_PRICING.copy()


def get_pricing():
    """Get current pricing dictionary."""
    return current_pricing.copy()


def update_pricing(new_pricing: dict):
    """Update pricing dictionary with new values."""
    global current_pricing
    for key, value in new_pricing.items():
        if key in current_pricing:
            current_pricing[key] = float(value)
    return current_pricing.copy()


def reset_pricing():
    """Reset pricing to defaults."""
    global current_pricing
    current_pricing = DEFAULT_PRICING.copy()
    return current_pricing.copy()


def calculate_costs(engineering_data: dict, pricing: dict = None) -> dict:
    """
    Calculate material and labour costs based on engineering estimates.

    Args:
        engineering_data: Dictionary containing engineering estimates
        pricing: Optional custom pricing dictionary

    Returns:
        Dictionary with cost breakdown
    """
    if pricing is None:
        pricing = current_pricing

    # Extract engineering values with defaults
    copper_weight = float(engineering_data.get("copper_weight_kg", 0) or 0)
    oil_quantity = float(engineering_data.get("oil_quantity_litres", 0) or 0)
    labour_hours = float(engineering_data.get("labour_hours", 0) or 0)
    bearing_count = int(engineering_data.get("bearing_count", 2) or 2)

    # Calculate individual costs
    copper_cost = copper_weight * pricing["copper_per_kg"]
    oil_cost = oil_quantity * pricing["oil_per_litre"]
    insulation_cost = pricing["insulation_paper"]
    varnish_cost = pricing["varnish"]
    labour_cost = labour_hours * pricing["labour_per_hour"]
    testing_cost = pricing["testing_charges"]
    painting_cost = pricing["painting_charges"]
    bearing_cost = bearing_count * pricing["bearing_cost"]
    transport_cost = pricing["transport_charges"]
    miscellaneous_cost = pricing["miscellaneous"]

    # Calculate subtotal
    subtotal = (
        copper_cost
        + oil_cost
        + insulation_cost
        + varnish_cost
        + labour_cost
        + testing_cost
        + painting_cost
        + bearing_cost
        + transport_cost
        + miscellaneous_cost
    )

    # Calculate GST
    gst_percentage = pricing["gst_percentage"]
    gst_amount = subtotal * (gst_percentage / 100)
    grand_total = subtotal + gst_amount

    cost_breakdown = {
        "items": [
            {
                "item": "Copper Wire",
                "quantity": f"{copper_weight} Kg",
                "unit_price": pricing["copper_per_kg"],
                "amount": round(copper_cost, 2),
            },
            {
                "item": "Insulation Paper",
                "quantity": "1 Set",
                "unit_price": pricing["insulation_paper"],
                "amount": round(insulation_cost, 2),
            },
            {
                "item": "Varnish",
                "quantity": "1 Set",
                "unit_price": pricing["varnish"],
                "amount": round(varnish_cost, 2),
            },
            {
                "item": "Oil",
                "quantity": f"{oil_quantity} Litres",
                "unit_price": pricing["oil_per_litre"],
                "amount": round(oil_cost, 2),
            },
            {
                "item": "Bearings",
                "quantity": f"{bearing_count} Nos",
                "unit_price": pricing["bearing_cost"],
                "amount": round(bearing_cost, 2),
            },
            {
                "item": "Testing Charges",
                "quantity": "1",
                "unit_price": pricing["testing_charges"],
                "amount": round(testing_cost, 2),
            },
            {
                "item": "Painting",
                "quantity": "1",
                "unit_price": pricing["painting_charges"],
                "amount": round(painting_cost, 2),
            },
            {
                "item": "Transport",
                "quantity": "1",
                "unit_price": pricing["transport_charges"],
                "amount": round(transport_cost, 2),
            },
            {
                "item": "Labour",
                "quantity": f"{labour_hours} Hours",
                "unit_price": pricing["labour_per_hour"],
                "amount": round(labour_cost, 2),
            },
            {
                "item": "Miscellaneous",
                "quantity": "1",
                "unit_price": pricing["miscellaneous"],
                "amount": round(miscellaneous_cost, 2),
            },
        ],
        "subtotal": round(subtotal, 2),
        "gst_percentage": gst_percentage,
        "gst_amount": round(gst_amount, 2),
        "grand_total": round(grand_total, 2),
    }

    return cost_breakdown
