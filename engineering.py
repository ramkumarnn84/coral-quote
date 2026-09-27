"""
Engineering module for Industrial AI - Quotation Intelligence.
Handles manufacturer lookup and engineering estimation.
"""

import math

# Manufacturer knowledge database
MANUFACTURER_DATABASE = {
    "kirloskar": {
        "name": "Kirloskar Electric Co Ltd",
        "country": "India",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 8,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-2RS",
                "oil_litres": 2,
                "labour_hours": 12,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 18,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-2RS",
                "oil_litres": 4,
                "labour_hours": 18,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 35,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-2RS",
                "oil_litres": 6,
                "labour_hours": 28,
            },
            "50_to_100kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 55,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-2RS",
                "oil_litres": 10,
                "labour_hours": 40,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 85,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-2RS",
                "oil_litres": 15,
                "labour_hours": 56,
            },
        },
    },
    "abb": {
        "name": "ABB Ltd",
        "country": "Switzerland",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 7,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-2Z",
                "oil_litres": 2,
                "labour_hours": 14,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 16,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-2Z",
                "oil_litres": 4,
                "labour_hours": 20,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 32,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-2Z",
                "oil_litres": 7,
                "labour_hours": 30,
            },
            "50_to_100kw": {
                "slots": 54,
                "coils": 54,
                "copper_weight_kg": 52,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-2Z",
                "oil_litres": 11,
                "labour_hours": 42,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 80,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-2Z",
                "oil_litres": 16,
                "labour_hours": 58,
            },
        },
    },
    "siemens": {
        "name": "Siemens AG",
        "country": "Germany",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 7.5,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-C3",
                "oil_litres": 2,
                "labour_hours": 14,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 17,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-C3",
                "oil_litres": 4,
                "labour_hours": 20,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 34,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-C3",
                "oil_litres": 7,
                "labour_hours": 30,
            },
            "50_to_100kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 53,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-C3",
                "oil_litres": 11,
                "labour_hours": 44,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 82,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-C3",
                "oil_litres": 15,
                "labour_hours": 60,
            },
        },
    },
    "cg": {
        "name": "CG Power and Industrial Solutions",
        "country": "India",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 7,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-2RS",
                "oil_litres": 2,
                "labour_hours": 12,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 16,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-2RS",
                "oil_litres": 4,
                "labour_hours": 18,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 33,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-2RS",
                "oil_litres": 6,
                "labour_hours": 26,
            },
            "50_to_100kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 50,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-2RS",
                "oil_litres": 10,
                "labour_hours": 38,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 78,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-2RS",
                "oil_litres": 14,
                "labour_hours": 54,
            },
        },
    },
    "bharat bijlee": {
        "name": "Bharat Bijlee Ltd",
        "country": "India",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 7.5,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-2RS",
                "oil_litres": 2,
                "labour_hours": 12,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 17,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-2RS",
                "oil_litres": 4,
                "labour_hours": 18,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 34,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-2RS",
                "oil_litres": 6,
                "labour_hours": 28,
            },
            "50_to_100kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 52,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-2RS",
                "oil_litres": 10,
                "labour_hours": 40,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 80,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-2RS",
                "oil_litres": 14,
                "labour_hours": 56,
            },
        },
    },
    "weg": {
        "name": "WEG S.A.",
        "country": "Brazil",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 7,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-ZZ",
                "oil_litres": 2,
                "labour_hours": 12,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 15,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-ZZ",
                "oil_litres": 4,
                "labour_hours": 18,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 32,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-ZZ",
                "oil_litres": 6,
                "labour_hours": 26,
            },
            "50_to_100kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 50,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-ZZ",
                "oil_litres": 10,
                "labour_hours": 38,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 78,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-ZZ",
                "oil_litres": 14,
                "labour_hours": 54,
            },
        },
    },
    "crompton": {
        "name": "Crompton Greaves",
        "country": "India",
        "specs_by_power": {
            "up_to_5kw": {
                "slots": 24,
                "coils": 24,
                "copper_weight_kg": 7,
                "wire_gauge": "SWG 18",
                "rotor_winding": "Cage",
                "bearing_type": "6205-2RS",
                "oil_litres": 2,
                "labour_hours": 12,
            },
            "5_to_15kw": {
                "slots": 36,
                "coils": 36,
                "copper_weight_kg": 16,
                "wire_gauge": "SWG 16",
                "rotor_winding": "Cage",
                "bearing_type": "6208-2RS",
                "oil_litres": 4,
                "labour_hours": 18,
            },
            "15_to_50kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 33,
                "wire_gauge": "SWG 14",
                "rotor_winding": "Cage",
                "bearing_type": "6310-2RS",
                "oil_litres": 6,
                "labour_hours": 26,
            },
            "50_to_100kw": {
                "slots": 48,
                "coils": 48,
                "copper_weight_kg": 51,
                "wire_gauge": "SWG 12",
                "rotor_winding": "Wound",
                "bearing_type": "6312-2RS",
                "oil_litres": 10,
                "labour_hours": 38,
            },
            "above_100kw": {
                "slots": 60,
                "coils": 60,
                "copper_weight_kg": 79,
                "wire_gauge": "SWG 10",
                "rotor_winding": "Wound",
                "bearing_type": "6316-2RS",
                "oil_litres": 14,
                "labour_hours": 54,
            },
        },
    },
}


def get_power_range(power_str: str) -> str:
    """Determine power range from power string."""
    if not power_str:
        return "15_to_50kw"

    # Extract numeric value from power string
    power_val = 0
    try:
        # Handle KVA, KW, HP values
        cleaned = power_str.upper().replace("KVA", "").replace("KW", "").replace("HP", "").strip()
        power_val = float(cleaned)

        # Convert HP to KW if needed (rough)
        if "HP" in power_str.upper():
            power_val = power_val * 0.746

        # KVA to KW approximation (0.8 PF)
        if "KVA" in power_str.upper():
            power_val = power_val * 0.8
    except (ValueError, TypeError):
        return "15_to_50kw"

    if power_val <= 5:
        return "up_to_5kw"
    elif power_val <= 15:
        return "5_to_15kw"
    elif power_val <= 50:
        return "15_to_50kw"
    elif power_val <= 100:
        return "50_to_100kw"
    else:
        return "above_100kw"


def lookup_manufacturer(manufacturer: str, power: str) -> dict:
    """
    Look up manufacturer specifications from local database.

    Args:
        manufacturer: Manufacturer name
        power: Power rating string

    Returns:
        Dictionary with manufacturer specs or None
    """
    if not manufacturer:
        return None

    # Normalize manufacturer name for lookup
    mfr_key = manufacturer.lower().strip()

    # Try to find matching manufacturer
    matched_key = None
    for key in MANUFACTURER_DATABASE:
        if key in mfr_key or mfr_key in key:
            matched_key = key
            break

    if not matched_key:
        return None

    mfr_data = MANUFACTURER_DATABASE[matched_key]
    power_range = get_power_range(power)
    specs = mfr_data["specs_by_power"].get(power_range, {})

    return {
        "manufacturer_name": mfr_data["name"],
        "country": mfr_data["country"],
        "source": "Retrieved",
        "specs": specs,
    }


def estimate_engineering(extracted_data: dict, manufacturer_data: dict = None) -> dict:
    """
    Estimate engineering values based on extracted data and manufacturer lookup.

    Args:
        extracted_data: Data extracted from nameplate by Vision AI
        manufacturer_data: Optional manufacturer lookup data

    Returns:
        Dictionary with engineering estimates and confidence levels
    """
    power = extracted_data.get("power") or extracted_data.get("kva") or ""
    voltage = extracted_data.get("voltage") or ""
    current = extracted_data.get("current") or extracted_data.get("amps") or ""
    rpm = extracted_data.get("rpm") or ""
    frequency = extracted_data.get("frequency") or ""

    # Base estimation from manufacturer data or general estimation
    if manufacturer_data and manufacturer_data.get("specs"):
        specs = manufacturer_data["specs"]
        base_confidence = 85
        source = "Retrieved from manufacturer database"
    else:
        # General estimation based on power
        power_range = get_power_range(power)
        specs = _general_estimation(power_range)
        base_confidence = 70
        source = "Estimated (manufacturer not in database)"

    # Calculate confidence adjustments
    confidence_boost = 0
    if voltage:
        confidence_boost += 3
    if current:
        confidence_boost += 3
    if rpm:
        confidence_boost += 2
    if frequency:
        confidence_boost += 2

    final_confidence = min(95, base_confidence + confidence_boost)

    engineering_result = {
        "copper_weight_kg": specs.get("copper_weight_kg", 30),
        "copper_weight_confidence": final_confidence,
        "wire_gauge": specs.get("wire_gauge", "SWG 14"),
        "wire_gauge_confidence": final_confidence - 5,
        "number_of_coils": specs.get("coils", 36),
        "number_of_coils_confidence": final_confidence,
        "number_of_slots": specs.get("slots", 36),
        "number_of_slots_confidence": final_confidence,
        "oil_quantity_litres": specs.get("oil_litres", 5),
        "oil_quantity_confidence": final_confidence - 5,
        "insulation_type": "Class F (Nomex)",
        "insulation_confidence": 90,
        "bearing_type": specs.get("bearing_type", "6310-2RS"),
        "bearing_confidence": final_confidence - 10,
        "bearing_count": 2,
        "rotor_winding": specs.get("rotor_winding", "Cage"),
        "rotor_condition": "Inspection Required",
        "stator_condition": "Rewinding Required",
        "labour_hours": specs.get("labour_hours", 24),
        "labour_confidence": final_confidence - 8,
        "testing_required": True,
        "painting_required": True,
        "overall_confidence": final_confidence,
        "estimation_source": source,
    }

    return engineering_result


def _general_estimation(power_range: str) -> dict:
    """General estimation when manufacturer is not in database."""
    general_specs = {
        "up_to_5kw": {
            "slots": 24,
            "coils": 24,
            "copper_weight_kg": 7,
            "wire_gauge": "SWG 18",
            "rotor_winding": "Cage",
            "bearing_type": "6205-2RS",
            "oil_litres": 2,
            "labour_hours": 12,
        },
        "5_to_15kw": {
            "slots": 36,
            "coils": 36,
            "copper_weight_kg": 16,
            "wire_gauge": "SWG 16",
            "rotor_winding": "Cage",
            "bearing_type": "6208-2RS",
            "oil_litres": 4,
            "labour_hours": 18,
        },
        "15_to_50kw": {
            "slots": 48,
            "coils": 48,
            "copper_weight_kg": 33,
            "wire_gauge": "SWG 14",
            "rotor_winding": "Cage",
            "bearing_type": "6310-2RS",
            "oil_litres": 6,
            "labour_hours": 26,
        },
        "50_to_100kw": {
            "slots": 48,
            "coils": 48,
            "copper_weight_kg": 52,
            "wire_gauge": "SWG 12",
            "rotor_winding": "Wound",
            "bearing_type": "6312-2RS",
            "oil_litres": 10,
            "labour_hours": 40,
        },
        "above_100kw": {
            "slots": 60,
            "coils": 60,
            "copper_weight_kg": 80,
            "wire_gauge": "SWG 10",
            "rotor_winding": "Wound",
            "bearing_type": "6316-2RS",
            "oil_litres": 15,
            "labour_hours": 56,
        },
    }
    return general_specs.get(power_range, general_specs["15_to_50kw"])
