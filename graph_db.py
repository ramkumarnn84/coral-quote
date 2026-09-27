"""
Neo4j Graph Database module for Industrial AI - Quotation Intelligence.
Stores quotation data as graph nodes and relationships for comparison and analytics.
"""

import os
import json
import logging
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

_driver = None


def get_driver():
    """Get or create Neo4j driver instance."""
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            _driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", NEO4J_URI)
        except Exception as e:
            logger.warning("Neo4j connection failed: %s. Graph features disabled.", str(e))
            _driver = None
    return _driver


def close_driver():
    """Close Neo4j driver."""
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def is_connected():
    """Check if Neo4j is available."""
    driver = get_driver()
    if driver is None:
        return False
    try:
        driver.verify_connectivity()
        return True
    except Exception:
        return False


def save_quotation_to_graph(quotation_data: dict, proposal_path: str = None):
    """
    Save a quotation as a graph node in Neo4j with relationships.

    Creates:
    - Quotation node with cost/engineering properties
    - Motor node with nameplate data
    - Manufacturer node
    - Relationships: (Quotation)-[:FOR_MOTOR]->(Motor)-[:MADE_BY]->(Manufacturer)
    - (Quotation)-[:HAS_PROPOSAL]->(Proposal) if proposal_path provided

    Args:
        quotation_data: Complete quotation dictionary
        proposal_path: Path to saved proposal JSON file
    """
    driver = get_driver()
    if driver is None:
        logger.warning("Neo4j not available. Skipping graph save for %s", quotation_data.get("quotation_number"))
        return False

    try:
        with driver.session() as session:
            session.execute_write(_create_quotation_graph, quotation_data, proposal_path)
        logger.info("Saved quotation %s to Neo4j graph", quotation_data.get("quotation_number"))
        return True
    except Exception as e:
        logger.error("Failed to save quotation to Neo4j: %s", str(e))
        return False


def _create_quotation_graph(tx, quotation_data: dict, proposal_path: str = None):
    """Transaction function to create quotation graph."""
    motor_details = quotation_data.get("motor_details", {})
    engineering = quotation_data.get("engineering_details", {})
    cost = quotation_data.get("cost_breakdown", {})
    quotation_number = quotation_data.get("quotation_number", "")
    inventory_id = quotation_data.get("inventory_id", "")

    # Create/Merge Manufacturer node
    manufacturer = motor_details.get("manufacturer") or "Unknown"
    tx.run(
        """
        MERGE (m:Manufacturer {name: $name})
        ON CREATE SET m.created_date = datetime()
        """,
        name=manufacturer,
    )

    # Create/Merge Motor node
    tx.run(
        """
        MERGE (motor:Motor {inventory_id: $inventory_id})
        ON CREATE SET
            motor.manufacturer = $manufacturer,
            motor.model = $model,
            motor.equipment_type = $equipment_type,
            motor.power = $power,
            motor.voltage = $voltage,
            motor.current = $current,
            motor.rpm = $rpm,
            motor.frequency = $frequency,
            motor.phase = $phase,
            motor.power_factor = $power_factor,
            motor.frame_number = $frame_number,
            motor.serial_number = $serial_number,
            motor.insulation_class = $insulation_class,
            motor.connection = $connection,
            motor.duty = $duty,
            motor.created_date = datetime()
        ON MATCH SET
            motor.manufacturer = $manufacturer,
            motor.model = $model,
            motor.power = $power,
            motor.voltage = $voltage,
            motor.rpm = $rpm
        """,
        inventory_id=inventory_id,
        manufacturer=manufacturer,
        model=motor_details.get("model"),
        equipment_type=motor_details.get("equipment_type"),
        power=motor_details.get("power"),
        voltage=motor_details.get("voltage"),
        current=motor_details.get("current"),
        rpm=motor_details.get("rpm"),
        frequency=motor_details.get("frequency"),
        phase=motor_details.get("phase"),
        power_factor=motor_details.get("power_factor"),
        frame_number=motor_details.get("frame_number"),
        serial_number=motor_details.get("serial_number"),
        insulation_class=motor_details.get("insulation_class"),
        connection=motor_details.get("connection"),
        duty=motor_details.get("duty"),
    )

    # Create Motor -> Manufacturer relationship
    tx.run(
        """
        MATCH (motor:Motor {inventory_id: $inventory_id})
        MATCH (m:Manufacturer {name: $manufacturer})
        MERGE (motor)-[:MADE_BY]->(m)
        """,
        inventory_id=inventory_id,
        manufacturer=manufacturer,
    )

    # Create Quotation node
    tx.run(
        """
        MERGE (q:Quotation {quotation_number: $quotation_number})
        ON CREATE SET
            q.inventory_id = $inventory_id,
            q.subtotal = $subtotal,
            q.gst_amount = $gst_amount,
            q.grand_total = $grand_total,
            q.copper_weight_kg = $copper_weight_kg,
            q.number_of_coils = $number_of_coils,
            q.wire_gauge = $wire_gauge,
            q.oil_quantity_litres = $oil_quantity_litres,
            q.labour_hours = $labour_hours,
            q.overall_confidence = $overall_confidence,
            q.proposal_path = $proposal_path,
            q.created_date = datetime(),
            q.status = 'Generated'
        ON MATCH SET
            q.subtotal = $subtotal,
            q.gst_amount = $gst_amount,
            q.grand_total = $grand_total,
            q.proposal_path = $proposal_path
        """,
        quotation_number=quotation_number,
        inventory_id=inventory_id,
        subtotal=cost.get("subtotal", 0),
        gst_amount=cost.get("gst_amount", 0),
        grand_total=cost.get("grand_total", 0),
        copper_weight_kg=engineering.get("copper_weight_kg"),
        number_of_coils=engineering.get("number_of_coils"),
        wire_gauge=engineering.get("wire_gauge"),
        oil_quantity_litres=engineering.get("oil_quantity_litres"),
        labour_hours=engineering.get("labour_hours"),
        overall_confidence=engineering.get("overall_confidence"),
        proposal_path=proposal_path,
    )

    # Create Quotation -> Motor relationship
    tx.run(
        """
        MATCH (q:Quotation {quotation_number: $quotation_number})
        MATCH (motor:Motor {inventory_id: $inventory_id})
        MERGE (q)-[:FOR_MOTOR]->(motor)
        """,
        quotation_number=quotation_number,
        inventory_id=inventory_id,
    )


def get_quotations_from_graph():
    """Retrieve all quotations from Neo4j graph."""
    driver = get_driver()
    if driver is None:
        return []

    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (q:Quotation)-[:FOR_MOTOR]->(motor:Motor)-[:MADE_BY]->(mfr:Manufacturer)
                RETURN q, motor, mfr
                ORDER BY q.created_date DESC
                """
            )
            quotations = []
            for record in result:
                q = record["q"]
                motor = record["motor"]
                mfr = record["mfr"]
                quotations.append({
                    "quotation_number": q["quotation_number"],
                    "inventory_id": q["inventory_id"],
                    "manufacturer": mfr["name"],
                    "model": motor.get("model"),
                    "grand_total": q.get("grand_total", 0),
                    "status": q.get("status", "Generated"),
                    "proposal_path": q.get("proposal_path"),
                    "created_date": str(q.get("created_date", "")),
                })
            return quotations
    except Exception as e:
        logger.error("Failed to read quotations from Neo4j: %s", str(e))
        return []


def get_quotation_from_graph(quotation_number: str):
    """Get a single quotation with full details from Neo4j."""
    driver = get_driver()
    if driver is None:
        return None

    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (q:Quotation {quotation_number: $quotation_number})-[:FOR_MOTOR]->(motor:Motor)-[:MADE_BY]->(mfr:Manufacturer)
                RETURN q, motor, mfr
                """,
                quotation_number=quotation_number,
            )
            record = result.single()
            if not record:
                return None

            q = record["q"]
            motor = record["motor"]
            mfr = record["mfr"]

            return {
                "quotation_number": q["quotation_number"],
                "inventory_id": q["inventory_id"],
                "grand_total": q.get("grand_total", 0),
                "subtotal": q.get("subtotal", 0),
                "gst_amount": q.get("gst_amount", 0),
                "proposal_path": q.get("proposal_path"),
                "status": q.get("status"),
                "motor_details": dict(motor),
                "manufacturer": mfr["name"],
                "engineering_details": {
                    "copper_weight_kg": q.get("copper_weight_kg"),
                    "number_of_coils": q.get("number_of_coils"),
                    "wire_gauge": q.get("wire_gauge"),
                    "oil_quantity_litres": q.get("oil_quantity_litres"),
                    "labour_hours": q.get("labour_hours"),
                    "overall_confidence": q.get("overall_confidence"),
                },
            }
    except Exception as e:
        logger.error("Failed to get quotation from Neo4j: %s", str(e))
        return None


def compare_quotations_graph(qt_num_1: str, qt_num_2: str):
    """
    Compare two quotations using graph relationships.
    Returns structured comparison data.
    """
    driver = get_driver()
    if driver is None:
        return None

    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (q1:Quotation {quotation_number: $qt1})-[:FOR_MOTOR]->(m1:Motor)
                MATCH (q2:Quotation {quotation_number: $qt2})-[:FOR_MOTOR]->(m2:Motor)
                RETURN q1, m1, q2, m2
                """,
                qt1=qt_num_1,
                qt2=qt_num_2,
            )
            record = result.single()
            if not record:
                return None

            return {
                "quotation_1": {
                    "quotation_number": record["q1"]["quotation_number"],
                    "grand_total": record["q1"].get("grand_total", 0),
                    "motor": dict(record["m1"]),
                    "engineering": {
                        "copper_weight_kg": record["q1"].get("copper_weight_kg"),
                        "number_of_coils": record["q1"].get("number_of_coils"),
                        "labour_hours": record["q1"].get("labour_hours"),
                    },
                },
                "quotation_2": {
                    "quotation_number": record["q2"]["quotation_number"],
                    "grand_total": record["q2"].get("grand_total", 0),
                    "motor": dict(record["m2"]),
                    "engineering": {
                        "copper_weight_kg": record["q2"].get("copper_weight_kg"),
                        "number_of_coils": record["q2"].get("number_of_coils"),
                        "labour_hours": record["q2"].get("labour_hours"),
                    },
                },
            }
    except Exception as e:
        logger.error("Failed to compare quotations in Neo4j: %s", str(e))
        return None
