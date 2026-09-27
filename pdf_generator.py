"""
PDF Generator module for Industrial AI - Quotation Intelligence.
Generates professional quotation PDFs using ReportLab.
"""

import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import config


def generate_pdf(quotation_data: dict) -> str:
    """
    Generate a professional quotation PDF.

    Args:
        quotation_data: Complete quotation data dictionary

    Returns:
        Path to the generated PDF file
    """
    quotation_number = quotation_data["quotation_number"]
    pdf_filename = f"{quotation_number}.pdf"
    pdf_path = os.path.join(config.QUOTATION_DIR, pdf_filename)

    # Ensure quotations directory exists
    os.makedirs(config.QUOTATION_DIR, exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CompanyName",
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a237e"),
        alignment=TA_CENTER,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="CompanySubtitle",
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#424242"),
        alignment=TA_CENTER,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="QuotationTitle",
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a237e"),
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a237e"),
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="NormalRight",
        fontSize=9,
        fontName="Helvetica",
        alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        fontSize=8,
        fontName="Helvetica",
        textColor=colors.HexColor("#616161"),
    ))
    styles.add(ParagraphStyle(
        name="TermsText",
        fontSize=8,
        fontName="Helvetica",
        textColor=colors.HexColor("#424242"),
        leftIndent=10,
        spaceAfter=3,
    ))

    elements = []

    # === HEADER ===
    elements.append(Paragraph(config.COMPANY_NAME, styles["CompanyName"]))
    elements.append(Paragraph(config.COMPANY_ADDRESS, styles["CompanySubtitle"]))
    elements.append(Paragraph(
        f"Phone: {config.COMPANY_PHONE} | Email: {config.COMPANY_EMAIL} | Web: {config.COMPANY_WEBSITE}",
        styles["CompanySubtitle"]
    ))
    elements.append(HRFlowable(
        width="100%", thickness=2, color=colors.HexColor("#1a237e"),
        spaceBefore=8, spaceAfter=8
    ))

    # === QUOTATION INFO ===
    elements.append(Paragraph("REWINDING QUOTATION", styles["QuotationTitle"]))

    created_date = quotation_data.get("created_date", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
    validity_date = (datetime.utcnow() + timedelta(days=config.QUOTATION_VALIDITY_DAYS)).strftime("%Y-%m-%d")

    info_data = [
        ["Quotation No:", quotation_number, "Date:", created_date],
        ["Inventory ID:", quotation_data["inventory_id"], "Valid Until:", validity_date],
        ["Prepared By:", config.COMPANY_NAME, "", ""],
    ]
    info_table = Table(info_data, colWidths=[80, 170, 70, 150])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # === MOTOR IMAGE ===
    image_path = quotation_data.get("image_path")
    if image_path and os.path.exists(image_path):
        try:
            img = Image(image_path, width=2.5 * inch, height=2 * inch)
            img.hAlign = "CENTER"
            elements.append(img)
            elements.append(Spacer(1, 8))
        except Exception:
            pass

    # === MOTOR DETAILS ===
    elements.append(Paragraph("MOTOR / GENERATOR DETAILS", styles["SectionHeader"]))

    motor_details = quotation_data.get("motor_details", {})
    motor_data = []
    motor_fields = [
        ("Manufacturer", "manufacturer"),
        ("Model", "model"),
        ("Equipment Type", "equipment_type"),
        ("Power", "power"),
        ("Voltage", "voltage"),
        ("Current", "current"),
        ("RPM", "rpm"),
        ("Frequency", "frequency"),
        ("Phase", "phase"),
        ("Power Factor", "power_factor"),
        ("Frame", "frame_number"),
        ("Serial Number", "serial_number"),
        ("Duty", "duty"),
        ("Insulation Class", "insulation_class"),
        ("Connection", "connection"),
    ]

    # Create 2-column motor details table
    row = []
    for label, key in motor_fields:
        value = motor_details.get(key) or "N/A"
        row.append(f"{label}:")
        row.append(str(value))
        if len(row) == 4:
            motor_data.append(row)
            row = []
    if row:
        while len(row) < 4:
            row.append("")
        motor_data.append(row)

    if motor_data:
        motor_table = Table(motor_data, colWidths=[90, 145, 90, 145])
        motor_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f5f5f5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(motor_table)

    # === ENGINEERING DETAILS ===
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("ENGINEERING DETAILS", styles["SectionHeader"]))

    eng_details = quotation_data.get("engineering_details", {})
    eng_data = [
        ["Parameter", "Value", "Confidence"],
        ["Copper Weight", f"{eng_details.get('copper_weight_kg', 'N/A')} Kg", f"{eng_details.get('copper_weight_confidence', 'N/A')}%"],
        ["Number of Coils", str(eng_details.get("number_of_coils", "N/A")), f"{eng_details.get('number_of_coils_confidence', 'N/A')}%"],
        ["Wire Gauge", str(eng_details.get("wire_gauge", "N/A")), f"{eng_details.get('wire_gauge_confidence', 'N/A')}%"],
        ["Oil Quantity", f"{eng_details.get('oil_quantity_litres', 'N/A')} Litres", f"{eng_details.get('oil_quantity_confidence', 'N/A')}%"],
        ["Insulation Type", str(eng_details.get("insulation_type", "N/A")), f"{eng_details.get('insulation_confidence', 'N/A')}%"],
        ["Bearing Type", str(eng_details.get("bearing_type", "N/A")), f"{eng_details.get('bearing_confidence', 'N/A')}%"],
        ["Rotor Condition", str(eng_details.get("rotor_condition", "N/A")), "-"],
        ["Stator Condition", str(eng_details.get("stator_condition", "N/A")), "-"],
        ["Labour Hours", str(eng_details.get("labour_hours", "N/A")), f"{eng_details.get('labour_confidence', 'N/A')}%"],
    ]

    eng_table = Table(eng_data, colWidths=[150, 180, 80])
    eng_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    elements.append(eng_table)

    # === COST TABLE ===
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("COST BREAKDOWN", styles["SectionHeader"]))

    cost_breakdown = quotation_data.get("cost_breakdown", {})
    cost_items = cost_breakdown.get("items", [])

    cost_data = [["S.No", "Item", "Quantity", "Unit Price (₹)", "Amount (₹)"]]
    for i, item in enumerate(cost_items, 1):
        cost_data.append([
            str(i),
            item["item"],
            str(item["quantity"]),
            f"₹ {item['unit_price']:,.2f}",
            f"₹ {item['amount']:,.2f}",
        ])

    # Add subtotal, GST, Grand Total
    cost_data.append(["", "", "", "Subtotal:", f"₹ {cost_breakdown.get('subtotal', 0):,.2f}"])
    cost_data.append(["", "", "", f"GST ({cost_breakdown.get('gst_percentage', 18)}%):", f"₹ {cost_breakdown.get('gst_amount', 0):,.2f}"])
    cost_data.append(["", "", "", "GRAND TOTAL:", f"₹ {cost_breakdown.get('grand_total', 0):,.2f}"])

    cost_table = Table(cost_data, colWidths=[30, 140, 70, 90, 90])
    cost_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -4), 0.5, colors.HexColor("#e0e0e0")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, colors.HexColor("#f8f9fa")]),
        # Subtotal row
        ("FONTNAME", (3, -3), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (3, -3), (-1, -3), 1, colors.HexColor("#1a237e")),
        # Grand total row
        ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (3, -1), (-1, -1), 10),
        ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#e8eaf6")),
    ]))
    elements.append(cost_table)

    # === TERMS AND CONDITIONS ===
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("TERMS & CONDITIONS", styles["SectionHeader"]))
    terms = [
        f"1. This quotation is valid for {config.QUOTATION_VALIDITY_DAYS} days from the date of issue.",
        "2. Material costs are subject to market fluctuation.",
        "3. Final cost may change after dismantling and inspection.",
        "4. Customer approval is required before commencing repair work.",
        "5. Payment terms: 50% advance, 50% on completion.",
        "6. Warranty: 12 months from date of delivery for rewinding work.",
        "7. Delivery timeline will be communicated after inspection.",
    ]
    for term in terms:
        elements.append(Paragraph(term, styles["TermsText"]))

    # === SIGNATURE ===
    elements.append(Spacer(1, 30))
    sig_data = [
        ["", ""],
        ["Customer Signature", "For " + config.COMPANY_NAME],
        ["", "Authorized Signatory"],
    ]
    sig_table = Table(sig_data, colWidths=[235, 235])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("LINEABOVE", (0, 1), (0, 1), 1, colors.black),
        ("LINEABOVE", (1, 1), (1, 1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, 0), 30),
    ]))
    elements.append(sig_table)

    # Build PDF
    doc.build(elements)

    return pdf_path
