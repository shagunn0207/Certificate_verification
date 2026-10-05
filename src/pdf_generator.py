"""
Official MSRIT Feedback on Training PDF Generator.
Generates an authentic A4 PDF matching the institutional layout from media_1791211291171.png.
"""
import os
import io
import re
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

def sanitize_filename(name: str) -> str:
    """Sanitize string for safe filenames."""
    if not name:
        return "Unknown"
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean or "Document"

import html

def format_pdf_text(text: Any, default_if_empty: str = "") -> str:
    """
    Safely format text for ReportLab Paragraph:
    - Escapes XML entities (&, <, >) to avoid Expat XML parsing errors with ampersands, quotes, brackets.
    - Converts newlines (\r\n or \n) to <br/> to preserve multi-line logical formatting.
    - Avoids injecting unwanted default placeholder strings.
    """
    if text is None:
        return default_if_empty
    val = str(text).strip()
    if not val:
        return default_if_empty
    # Escape XML entities
    escaped = html.escape(val)
    # Convert newlines to ReportLab breaks
    formatted = escaped.replace("\r\n", "<br/>").replace("\n", "<br/>")
    return formatted

def generate_training_feedback_pdf(feedback_data: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
    """
    Generates a genuine A4 PDF of the official MSRIT Feedback on Training document
    using the CURRENT form state.
    """
    buffer = io.BytesIO()
    # A4 margins: 36 pt (0.5 in) left/right, 36 pt top/bottom
    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Base typography (Times-Roman formal styling)
    ref_style = ParagraphStyle(
        'RefStyle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=12,
        alignment=TA_RIGHT,
        textColor=colors.black
    )

    title_main_style = ParagraphStyle(
        'TitleMain',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=9.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=10
    )

    doc_header_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=14
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    body_bold_style = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    italic_caption_style = ParagraphStyle(
        'ItalicCaption',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=8.5,
        leading=11,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#475569')
    )

    box_text_style = ParagraphStyle(
        'BoxText',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # 1. Reference Code (Top-Right)
    story.append(Paragraph("MSRIT/IQAC/2026/FBT", ref_style))
    story.append(Spacer(1, 4))

    # 2. Header: Logo & Title
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, "assets", "msrit_logo.png")
    if os.path.exists(logo_path):
        try:
            # 170 x 40 pt logo display
            logo_img = Image(logo_path, width=170, height=40)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 6))
        except Exception:
            pass

    story.append(Paragraph("MS RAMAIAH INSTITUTE OF TECHNOLOGY, BANGALORE – 54", title_main_style))
    story.append(Paragraph("(Autonomous institute Affiliated to VTU)", subtitle_style))
    story.append(Paragraph("<u>FEEDBACK ON TRAINING</u>", doc_header_style))
    story.append(Spacer(1, 8))

    # Current form values from single source of truth
    emp_name = format_pdf_text(feedback_data.get("Faculty Name", ""))
    training_date = format_pdf_text(feedback_data.get("Training Date", ""))
    dept = format_pdf_text(feedback_data.get("Department", ""))
    prog_name = format_pdf_text(feedback_data.get("Training Program", ""))
    pres_rating = format_pdf_text(feedback_data.get("Presentation Rating", "Good"))
    und_level = format_pdf_text(feedback_data.get("Understanding Level", "Good"))
    future_prog = format_pdf_text(feedback_data.get("Future Programs", "Yes"))
    status = str(feedback_data.get("Feedback Status", "DRAFT")).upper()

    cov_topics = str(feedback_data.get("Coverage of Topics", "") or "")
    und_reason = str(feedback_data.get("Understanding Reason", "") or "")
    rec_topics = str(feedback_data.get("Recommended Topics", "") or "")

    # 3. Employee Details (Table Layout)
    row1 = [
        Paragraph(f"<b>Name of the Employee:</b> {emp_name}", body_style),
        Paragraph(f"<b>Date of Training:</b> {training_date}", body_style)
    ]
    row2 = [
        Paragraph(f"<b>Department:</b> {dept}", body_style),
        Paragraph("", body_style)
    ]
    row3 = [
        Paragraph(f"<b>Name of the Training Program:</b> {prog_name}", body_style),
        Paragraph("", body_style)
    ]

    t_details = Table([row1, row2, row3], colWidths=[310, 205])
    t_details.setStyle(TableStyle([
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (0, 2), (1, 2)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_details)
    story.append(Spacer(1, 10))

    # 4. Feedback Section
    story.append(Paragraph("<b>Feedback:</b>", section_heading_style))

    # a) Presentation by faculty
    story.append(Paragraph(f"<b>a) Presentation by faculty :</b> &nbsp;&nbsp;<u>{pres_rating}</u> &nbsp;&nbsp;<font size=8 color='#666666'>(Excellent / Good / Average / Poor / Very Poor)</font>", body_style))
    story.append(Spacer(1, 6))

    # b) Coverage of topics (dynamic height, no placeholders, full multi-line wrap)
    story.append(Paragraph("<b>b) Coverage of topics :</b>", body_style))
    cov_formatted = format_pdf_text(cov_topics)
    cov_row_height = [32] if not cov_topics.strip() else None
    t_cov = Table([[Paragraph(cov_formatted, box_text_style)]], colWidths=[515], rowHeights=cov_row_height)
    t_cov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cov)
    story.append(Spacer(1, 8))

    # c) Level of understanding
    story.append(Paragraph(f"<b>c) Your level of understanding :</b> &nbsp;&nbsp;<u>{und_level}</u> &nbsp;&nbsp;<font size=8 color='#666666'>(Good / Average / Poor)</font>", body_style))
    story.append(Paragraph("(Specify briefly reasons)", italic_caption_style))
    story.append(Spacer(1, 2))
    und_formatted = format_pdf_text(und_reason)
    und_row_height = [32] if not und_reason.strip() else None
    t_und = Table([[Paragraph(und_formatted, box_text_style)]], colWidths=[515], rowHeights=und_row_height)
    t_und.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_und)
    story.append(Spacer(1, 8))

    # d) Do you want such programs in future
    story.append(Paragraph(f"<b>d) Do you want such programs in future :</b> &nbsp;&nbsp;<u>{future_prog}</u> &nbsp;&nbsp;<font size=8 color='#666666'>(Yes / No)</font>", body_style))
    story.append(Paragraph("If yes, what topics would you recommend?", italic_caption_style))
    story.append(Spacer(1, 2))
    rec_default = "N/A" if future_prog == "No" and not rec_topics.strip() else ""
    rec_formatted = format_pdf_text(rec_topics, default_if_empty=rec_default)
    rec_row_height = [28] if not rec_topics.strip() and not rec_default else None
    t_rec = Table([[Paragraph(rec_formatted, box_text_style)]], colWidths=[515], rowHeights=rec_row_height)
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_rec)
    story.append(Spacer(1, 10))

    # Double Line Divider
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=0, spaceAfter=2))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=0, spaceAfter=10))

    # 5. HOD Evaluation Section
    story.append(Paragraph("<b>HOD’s evaluation of the effectiveness of training</b>", section_heading_style))
    story.append(Paragraph("(to be filled in about three months after the training)", italic_caption_style))
    story.append(Spacer(1, 6))

    hod_row1 = [
        Paragraph("<b>a) Understanding:</b>", body_style),
        Paragraph("Good / Average / Poor", body_style)
    ]
    hod_row2 = [
        Paragraph("<b>b) Application at Job:</b>", body_style),
        Paragraph("Applies well / No evidence of application /<br/>Exhibits Lack of understanding / Indifferent though knowledgeable", body_style)
    ]
    t_hod_eval = Table([hod_row1, hod_row2], colWidths=[130, 385])
    t_hod_eval.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_hod_eval)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>c) General Remarks:</b>", body_style))
    story.append(Spacer(1, 2))
    hod_remarks_text = "Pending HOD Evaluation — to be completed approximately three months after training."
    t_hod_rem = Table([[Paragraph(f"<i>{hod_remarks_text}</i>", italic_caption_style)]], colWidths=[515])
    t_hod_rem.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_hod_rem)
    story.append(Spacer(1, 14))

    # Divider before signatures
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=0, spaceAfter=22))

    # 6. Signatures Section
    sig_fac_text = "<b>Signature of the Faculty</b><br/><font size=8 color='#64748b'>" + (
        "Status: Verified Faculty Submission" if status in ["SUBMITTED", "APPROVED"] else "Status: Pending Signature"
    ) + "</font>"

    sig_hod_text = "<b>Signature of the HOD</b><br/><font size=8 color='#64748b'>" + (
        f"Status: Approved on {feedback_data.get('Approved At', '')}" if status == "APPROVED" else "Status: Pending HOD Signature"
    ) + "</font>"

    t_sigs = Table([[
        Paragraph(sig_fac_text, body_style),
        Paragraph(sig_hod_text, ParagraphStyle('SigRight', parent=body_style, alignment=TA_RIGHT))
    ]], colWidths=[255, 260])
    t_sigs.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_sigs)

    # Build PDF
    doc.build(story)

    if not output_path:
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    return b""
