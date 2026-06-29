"""
Generates a professional, branded PDF report for a single prediction record.
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)

PRIMARY = colors.HexColor("#2563EB")
SECONDARY = colors.HexColor("#0EA5E9")
ACCENT = colors.HexColor("#14B8A6")
SUCCESS = colors.HexColor("#22C55E")
WARNING = colors.HexColor("#F59E0B")
DANGER = colors.HexColor("#EF4444")
SLATE = colors.HexColor("#475569")
BG = colors.HexColor("#F8FAFC")

RISK_COLOR = {"Low": SUCCESS, "Medium": WARNING, "High": DANGER}


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="BrandTitle", fontSize=20, leading=24, textColor=PRIMARY,
                           fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle(name="BrandSub", fontSize=10, textColor=SLATE, fontName="Helvetica"))
    ss.add(ParagraphStyle(name="SectionHeader", fontSize=13, leading=16, textColor=PRIMARY,
                           fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle(name="Body", fontSize=10, leading=15, textColor=colors.HexColor("#1E293B")))
    ss.add(ParagraphStyle(name="Small", fontSize=8.5, leading=12, textColor=SLATE))
    return ss


def generate_pdf_report(record, user, output_path: str):
    """record: PredictionRecord instance, user: User instance"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
        title="Liver Disease Prediction Report",
    )
    story = []

    # --- Header -----------------------------------------------------
    header_table = Table(
        [[Paragraph("LiverPredict AI", styles["BrandTitle"]),
          Paragraph(f"Report generated<br/>{datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                    ParagraphStyle(name="r", parent=styles["BrandSub"], alignment=TA_LEFT))]],
        colWidths=[110 * mm, 60 * mm],
    )
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(header_table)
    story.append(Paragraph("Intelligent ICT-Based Liver Disease Prediction System", styles["BrandSub"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=PRIMARY))
    story.append(Spacer(1, 10))

    # --- Patient details ----------------------------------------------
    story.append(Paragraph("Patient Information", styles["SectionHeader"]))
    patient_data = [
        ["Full Name", user.full_name, "Email", user.email],
        ["Age", str(record.age), "Gender", record.gender or "-"],
        ["Phone", user.phone or "-", "Report Date", record.created_at.strftime("%d %b %Y, %I:%M %p")],
    ]
    pt = Table(patient_data, colWidths=[28 * mm, 57 * mm, 28 * mm, 57 * mm])
    pt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE),
        ("TEXTCOLOR", (2, 0), (2, -1), SLATE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (-1, -1), BG),
    ]))
    story.append(pt)
    story.append(Spacer(1, 10))

    # --- Result banner --------------------------------------------------
    risk_color = RISK_COLOR.get(record.risk_level, SLATE)
    result_table = Table(
        [[Paragraph(f"<b>{record.prediction}</b>", ParagraphStyle(
            name="res", fontSize=14, textColor=colors.white, fontName="Helvetica-Bold")),
          Paragraph(f"Risk Level: <b>{record.risk_level}</b>", ParagraphStyle(
              name="risk", fontSize=11, textColor=colors.white)),
          Paragraph(f"Confidence: <b>{record.confidence}%</b>", ParagraphStyle(
              name="conf", fontSize=11, textColor=colors.white, alignment=TA_CENTER))]],
        colWidths=[70 * mm, 50 * mm, 50 * mm],
    )
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), risk_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 12))

    # --- Test parameters --------------------------------------------
    story.append(Paragraph("Liver Test Parameters", styles["SectionHeader"]))
    params = [
        ("Total Bilirubin", f"{record.total_bilirubin} mg/dL"),
        ("Direct Bilirubin", f"{record.direct_bilirubin} mg/dL"),
        ("Alkaline Phosphatase", f"{record.alkaline_phosphotase} IU/L"),
        ("ALT (Alamine Aminotransferase)", f"{record.alt} IU/L"),
        ("AST (Aspartate Aminotransferase)", f"{record.ast} IU/L"),
        ("Total Protein", f"{record.total_proteins} g/dL"),
        ("Albumin", f"{record.albumin} g/dL"),
        ("Albumin/Globulin Ratio", f"{record.ag_ratio}"),
    ]
    rows = []
    for i in range(0, len(params), 2):
        left = params[i]
        right = params[i + 1] if i + 1 < len(params) else ("", "")
        rows.append([left[0], left[1], right[0], right[1]])
    param_table = Table(rows, colWidths=[45 * mm, 25 * mm, 45 * mm, 25 * mm])
    param_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE),
        ("TEXTCOLOR", (2, 0), (2, -1), SLATE),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
    ]))
    story.append(param_table)
    story.append(Spacer(1, 10))

    # --- Interpretation -----------------------------------------------
    story.append(Paragraph("Health Interpretation", styles["SectionHeader"]))
    story.append(Paragraph(record.interpretation or "-", styles["Body"]))
    story.append(Spacer(1, 8))

    # --- Contributing factors ------------------------------------------
    story.append(Paragraph("Key Contributing Factors", styles["SectionHeader"]))
    for factor in record.factors_list():
        story.append(Paragraph(f"&bull;&nbsp; {factor}", styles["Body"]))
    story.append(Spacer(1, 8))

    # --- Recommendations -----------------------------------------------
    story.append(Paragraph("Personalized Recommendations", styles["SectionHeader"]))
    for rec in record.recommendations_list():
        story.append(Paragraph(f"&bull;&nbsp; {rec}", styles["Body"]))
    story.append(Spacer(1, 16))

    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#E2E8F0")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Disclaimer: This report is generated by an AI-assisted prediction system and is "
        "intended to support, not replace, professional medical diagnosis. Please consult "
        "a licensed physician for clinical decisions.",
        styles["Small"],
    ))
    story.append(Paragraph(
        f"Report ID: LP-{record.id:06d}  |  Generated by LiverPredict AI on "
        f"{datetime.now().strftime('%d %b %Y %I:%M %p')}",
        styles["Small"],
    ))

    doc.build(story)
    return output_path
