from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "clinic_faq_rag_demo.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#1B7F79")
INK = colors.HexColor("#23313D")
PALE = colors.HexColor("#E8F4F2")
LINE = colors.HexColor("#D7E0E6")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=32, textColor=NAVY, spaceAfter=14))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY, spaceAfter=10))
styles.add(ParagraphStyle(name="H2X", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=TEAL, spaceAfter=7))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name="BulletX", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12.5, leftIndent=12, bulletIndent=1, textColor=INK, spaceAfter=4))


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 13 * mm, A4[0], 13 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawString(18 * mm, A4[1] - 8.5 * mm, "NORTHSTAR DEMO CLINIC")
        canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 8.5 * mm, "FAQ knowledge base")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFillColor(colors.HexColor("#5E6B75"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 9.5 * mm, "FICTIONAL DEMO - NOT MEDICAL ADVICE")
    canvas.drawRightString(A4[0] - 18 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def box(title, body):
    table = Table([[Paragraph(f"<b>{title}</b>", styles["BodyX"]), Paragraph(body, styles["BodyX"])]], colWidths=[42 * mm, 123 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 8)]))
    return table


def bullets(items):
    return [Paragraph(item, styles["BulletX"], bulletText="-") for item in items]


def service(code, name, description, preparation, bring, after, keywords):
    return [
        Paragraph(name, styles["H2X"]),
        box("RAG metadata", f"Service code: <b>{code}</b><br/>Keywords: {keywords}"),
        Spacer(1, 6),
        Paragraph(description, styles["BodyX"]),
        Paragraph("<b>Before the visit</b>", styles["BodyX"]),
        *bullets(preparation),
        Paragraph("<b>Bring with you</b>", styles["BodyX"]),
        *bullets(bring),
        Paragraph(f"<b>After the visit:</b> {after}", styles["BodyX"]),
    ]


services = [
    ("CONSULT-01", "General consultation", "A planned non-emergency conversation with a clinician to review existing information and agree on appropriate next steps.", ["Write down the questions you want to discuss.", "Collect relevant prior reports.", "Continue routine medication unless qualified staff gave different instructions."], ["Photo ID and insurance information if applicable.", "Medication and allergy list.", "Referral and prior reports if relevant."], "Qualified staff explain any next steps; booking alone does not confirm a diagnosis or treatment plan.", "consultation, clinician visit, follow-up, records review"),
    ("LAB-01", "Routine laboratory collection", "Collection of a sample that has already been ordered by an authorized clinician. The collection team does not choose which tests are needed.", ["Check the written order for exact preparation.", "Do not assume fasting is required; fast only when explicitly instructed.", "Do not change medication or fluid intake unless qualified staff instruct you."], ["Photo ID and laboratory order.", "Insurance information if applicable.", "Written preparation instructions."], "Result timing and interpretation must come from qualified staff.", "laboratory, blood draw, sample collection, fasting"),
    ("IMG-US-01", "Diagnostic ultrasound visit", "A non-emergency imaging appointment based on an existing order. Preparation varies by body area and exact exam.", ["Confirm the exact ultrasound type on the order.", "Follow only exam-specific written eating, drinking, bladder, or clothing instructions.", "If instructions are missing, contact the clinic rather than guessing."], ["Photo ID, imaging order, and prior imaging reports if available.", "Written exam-specific instructions."], "A qualified clinician reviews and explains results; the chatbot does not interpret images.", "ultrasound, sonography, imaging order, scan preparation"),
    ("IMG-XR-01", "Plain X-ray visit", "A scheduled radiography visit based on an existing order. Imaging staff confirm the requested body area and required safety checks.", ["Wear clothing that is easy to adjust around the requested area.", "Tell imaging staff about any possibility of pregnancy before imaging begins.", "Do not remove medical devices or change medication based on this guide."], ["Photo ID and imaging order.", "Previous imaging reports if requested."], "Staff explain how results are released but reception does not interpret them.", "x-ray, radiography, imaging, metal items"),
    ("PT-01", "Physical therapy initial assessment", "An introductory visit where a qualified therapist reviews the referral, goals, and relevant limitations.", ["Wear comfortable clothing that allows ordinary movement.", "Bring referral restrictions or recent reports.", "Do not attempt new exercises based only on this document."], ["Photo ID, referral, and prior reports.", "Medication list and existing clinician instructions."], "The therapist provides individualized instructions and explains whether follow-up is appropriate.", "physical therapy, physiotherapy, mobility, rehabilitation"),
    ("VAX-01", "Vaccination appointment", "A preventive appointment where qualified staff review eligibility, records, consent, and clinic policy before vaccination.", ["Do not change medication based on this guide.", "Contact staff in advance about accessibility or eligibility questions.", "Allow time for check-in and any staff-directed observation."], ["Photo ID, insurance information, and vaccination records.", "Requested consent documents."], "Qualified staff provide the official record and individual after-visit instructions.", "vaccination, vaccine, immunization, vaccine record"),
    ("BH-01", "Behavioral health intake", "A planned non-emergency introductory conversation to collect background information and explain service boundaries.", ["Complete securely supplied intake forms.", "Choose a private setting for a remote appointment when possible.", "Prepare provider contact details only if you choose to share them."], ["Photo ID and intake documents.", "Insurance and referral information if applicable."], "Symptom assessment, crisis language, treatment, and medication questions must be routed to humans.", "behavioral health, mental health, intake, private appointment"),
]

doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm, bottomMargin=18 * mm, title="Northstar Demo Clinic FAQ RAG Demo")
story = [Spacer(1, 30 * mm), Paragraph("NORTHSTAR DEMO CLINIC", styles["BodyX"]), Paragraph("Services and Visit Preparation Guide", styles["TitleX"]), Paragraph("Synthetic knowledge-base document for RAG testing. Version 1.0 - August 2026.", styles["BodyX"]), Spacer(1, 8 * mm), box("Important", "This clinic and all service details are fictional. This document is not medical advice. Preparation requirements vary; always follow written instructions from qualified clinic staff."), Spacer(1, 10 * mm), Paragraph("Document purpose", styles["H2X"]), Paragraph("A consistent sample source for administrative FAQ answers, retrieval testing, service descriptions, preparation checklists, and safe human handoff.", styles["BodyX"]), PageBreak()]
story += [Paragraph("General rules for every visit", styles["H1X"]), *bullets(["Arrive about 10 minutes early.", "Bring photo ID, insurance details if applicable, and any referral or order.", "Bring an up-to-date medication and allergy list.", "Tell staff if you need language, mobility, hearing, vision, or other access support.", "Service-specific written instructions take priority over this demo guide.", "Do not fast, restrict fluids, or change medication based only on this document.", "Urgent, symptom-related, treatment, and medication questions must go to a human-controlled flow."]), Spacer(1, 8), box("Safety boundary", "The receptionist chatbot may answer administrative preparation questions only. It must not diagnose, assess symptoms, prescribe, recommend treatment, or interpret results."), PageBreak()]
for index, data in enumerate(services):
    story.append(Paragraph("Service description and preparation", styles["H1X"]))
    story.extend(service(*data))
    if index != len(services) - 1:
        story.append(PageBreak())
story += [Spacer(1, 10), box("RAG response policy", "Use this document only for administrative service descriptions and preparation. Cite the service code, do not invent missing facts, and hand off when confidence is low or the question is medical."), Spacer(1, 10), Paragraph("Document ID: NSDC-KB-001 | Status: synthetic_demo | Review required: true", styles["BodyX"])]
doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
print(OUTPUT)
