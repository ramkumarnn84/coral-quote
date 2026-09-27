"""
Vision AI module for Industrial AI - Quotation Intelligence.
Uses stored data for known images; LLM integration to be added later.
"""

import base64
import hashlib
import json
import os
from openai import AsyncOpenAI
import config

# Stored results for known images (bypass LLM for now)
STORED_RESULTS = {
    "kirloskar_generator": {
        "extracted": {
            "manufacturer": "Kirloskar Electric Co Ltd",
            "model": "A.C. Generator",
            "frame_number": None,
            "serial_number": None,
            "power": None,
            "kva": "62.5",
            "voltage": "415",
            "current": None,
            "amps": "87",
            "frequency": "50",
            "rpm": "1500",
            "power_factor": "0.8",
            "phase": "3",
            "duty": "S1",
            "insulation_class": "F",
            "connection": "PH",
            "bearing_number": None,
            "country": "India",
            "manufacturer_address": "Kirloskar Electric Co Ltd, India",
            "equipment_type": "A.C. Generator",
            "cooling": "IC411",
            "protection": None,
            "weight": None
        },
        "estimated": {
            "copper_weight_kg": 35,
            "oil_quantity_litres": 6,
            "wire_gauge": "SWG 14",
            "number_of_coils": 48,
            "insulation_type": "Class F (Nomex)",
            "bearing_recommendation": "6310-2RS",
            "labour_hours": 28,
            "testing_charges": 3500,
            "painting_charges": 2500,
            "confidence_percentage": 92
        }
    }
}


def get_image_hash(file_path: str) -> str:
    """Get MD5 hash of image file for comparison."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


async def analyze_nameplate(image_path: str) -> dict:
    """
    Analyze motor nameplate image.
    Currently uses stored data. LLM integration to be added later.

    Args:
        image_path: Path to the uploaded image file

    Returns:
        Dictionary containing extracted and estimated data
    """
    # For now, return stored Kirloskar generator data for any image
    # This will be replaced with actual LLM call later
    return STORED_RESULTS["kirloskar_generator"]


async def analyze_nameplate_llm(image_path: str) -> dict:
    """
    Analyze motor nameplate image using GPT Vision API.
    To be used when LLM integration is enabled.
    """
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    SYSTEM_PROMPT = """You are a senior electrical motor engineer with 25 years of rewinding experience.

Read the uploaded motor/generator nameplate.
Extract every visible field.
If a field is not visible or unavailable, return null for that field.

Then estimate the following engineering values based on the motor specifications:
- Copper Weight (in Kg)
- Oil Quantity (in Litres)
- Wire Gauge (SWG)
- Number of Coils
- Insulation Type
- Bearing Recommendation
- Labour Hours
- Testing Charges (INR)
- Painting Charges (INR)
- Confidence Percentage (overall)

Clearly distinguish between:
- "extracted" - values directly read from nameplate
- "retrieved" - values from manufacturer database
- "estimated" - values calculated/guessed

Return ONLY valid JSON with this exact structure:
{
    "extracted": {
        "manufacturer": null,
        "model": null,
        "frame_number": null,
        "serial_number": null,
        "power": null,
        "kva": null,
        "voltage": null,
        "current": null,
        "amps": null,
        "frequency": null,
        "rpm": null,
        "power_factor": null,
        "phase": null,
        "duty": null,
        "insulation_class": null,
        "connection": null,
        "bearing_number": null,
        "country": null,
        "manufacturer_address": null,
        "equipment_type": null,
        "cooling": null,
        "protection": null,
        "weight": null
    },
    "estimated": {
        "copper_weight_kg": null,
        "oil_quantity_litres": null,
        "wire_gauge": null,
        "number_of_coils": null,
        "insulation_type": null,
        "bearing_recommendation": null,
        "labour_hours": null,
        "testing_charges": null,
        "painting_charges": null,
        "confidence_percentage": null
    }
}

Do not include any markdown formatting.
Do not include any explanation.
Return ONLY the JSON object."""

    # Read and encode image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_types.get(ext, "image/jpeg")

    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Read this motor/generator nameplate and extract all visible information. Return JSON only.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        max_tokens=2000,
        temperature=0.1,
    )

    response_text = response.choices[0].message.content.strip()

    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines)

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(response_text[start:end])
        else:
            raise ValueError("Failed to parse Vision API response as JSON")

    return result
