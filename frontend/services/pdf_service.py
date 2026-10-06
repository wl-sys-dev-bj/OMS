import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


# Colors
PRIMARY = colors.HexColor("#173c32")
ACCENT = colors.HexColor("#1767bd")
LINE_COLOR = colors.HexColor("#dce4de")
DARK_LINE = colors.HexColor("#222222")
BG_LIGHT = colors.HexColor("#f8faf7")
TEXT_DARK = colors.HexColor("#18352e")
MUTED = colors.HexColor("#666666")


def get_base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=PRIMARY,
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="FieldLabel",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#444444"),
    ))
    styles.add(ParagraphStyle(
        name="FieldValue",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK,
    ))
    styles.add(ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=TEXT_DARK,
    ))
    styles.add(ParagraphStyle(
        name="TableHead",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="JoiningTitle",
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=ACCENT,
    ))
    styles.add(ParagraphStyle(
        name="JoiningText",
        fontName="Times-Roman",
        fontSize=9,
        leading=12,
        textColor=DARK_LINE,
    ))
    styles.add(ParagraphStyle(
        name="JoiningBold",
        fontName="Times-Bold",
        fontSize=9,
        leading=12,
        textColor=DARK_LINE,
    ))
    return styles


def generate_employee_pdf(employee):
    """Generate official Employee Profile PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    custom_styles = get_base_styles()
    elements = []

    # Header / Letterhead
    header_data = [
        [
            Paragraph("<b>OMS WORKFORCE & PEOPLE OPERATIONS</b><br/><font size=8 color='#666'>Dubai, UAE · operations@oms.com · Official Employee Record</font>", styles["Normal"]),
            Paragraph(f"<b>EMPLOYEE PROFILE</b><br/><font size=9 color='#173c32'>ID: {employee.employee_id}</font>", ParagraphStyle('R', alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=12, textColor=PRIMARY))
        ]
    ]
    header_table = Table(header_data, colWidths=[120 * mm, 60 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))

    # Basic & Personal Details
    elements.append(Paragraph("1. PERSONAL INFORMATION", custom_styles["SectionHeader"]))
    personal_data = [
        [
            Paragraph("Full Name:", custom_styles["FieldLabel"]),
            Paragraph(employee.full_name or "—", custom_styles["FieldValue"]),
            Paragraph("Employee ID:", custom_styles["FieldLabel"]),
            Paragraph(employee.employee_id or "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Date of Birth:", custom_styles["FieldLabel"]),
            Paragraph(str(employee.date_of_birth) if employee.date_of_birth else "—", custom_styles["FieldValue"]),
            Paragraph("Gender:", custom_styles["FieldLabel"]),
            Paragraph(employee.get_gender_display() if employee.gender else "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Nationality:", custom_styles["FieldLabel"]),
            Paragraph(employee.nationality or "—", custom_styles["FieldValue"]),
            Paragraph("Marital Status:", custom_styles["FieldLabel"]),
            Paragraph(employee.get_marital_status_display() if employee.marital_status else "—", custom_styles["FieldValue"]),
        ],
    ]
    personal_table = Table(personal_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 8))

    # Employment Information
    elements.append(Paragraph("2. EMPLOYMENT & ASSIGNMENT", custom_styles["SectionHeader"]))
    dept_name = employee.department.name if employee.department else "—"
    desig_name = employee.designation.name if employee.designation else (employee.job_title or "—")
    employment_data = [
        [
            Paragraph("Department:", custom_styles["FieldLabel"]),
            Paragraph(dept_name, custom_styles["FieldValue"]),
            Paragraph("Designation / Title:", custom_styles["FieldLabel"]),
            Paragraph(desig_name, custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Employment Status:", custom_styles["FieldLabel"]),
            Paragraph(employee.get_status_display() if employee.status else "—", custom_styles["FieldValue"]),
            Paragraph("Employment Type:", custom_styles["FieldLabel"]),
            Paragraph(employee.get_employment_type_display() if employee.employment_type else "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Joining Date:", custom_styles["FieldLabel"]),
            Paragraph(str(employee.joining_date) if employee.joining_date else "—", custom_styles["FieldValue"]),
            Paragraph("Salary:", custom_styles["FieldLabel"]),
            Paragraph(f"AED {employee.salary:,.2f}" if employee.salary else "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Work Location:", custom_styles["FieldLabel"]),
            Paragraph(employee.work_location or "Dubai, UAE", custom_styles["FieldValue"]),
            Paragraph("Client Account:", custom_styles["FieldLabel"]),
            Paragraph(employee.client_name or "—", custom_styles["FieldValue"]),
        ],
    ]
    emp_table = Table(employment_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 8))

    # Contact & Identification
    elements.append(Paragraph("3. CONTACT & IDENTIFICATION", custom_styles["SectionHeader"]))
    contact_data = [
        [
            Paragraph("Phone Number:", custom_styles["FieldLabel"]),
            Paragraph(employee.phone or "—", custom_styles["FieldValue"]),
            Paragraph("Email Address:", custom_styles["FieldLabel"]),
            Paragraph(employee.email or "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Passport Number:", custom_styles["FieldLabel"]),
            Paragraph(employee.passport_number or "—", custom_styles["FieldValue"]),
            Paragraph("Citizenship / ID:", custom_styles["FieldLabel"]),
            Paragraph(employee.citizenship_number or "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Emergency Contact:", custom_styles["FieldLabel"]),
            Paragraph(f"{employee.emergency_contact_name} ({employee.emergency_contact_relationship})" if employee.emergency_contact_name else "—", custom_styles["FieldValue"]),
            Paragraph("Emergency Phone:", custom_styles["FieldLabel"]),
            Paragraph(employee.emergency_contact_phone or "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("Current Address:", custom_styles["FieldLabel"]),
            Paragraph(employee.current_address or "—", custom_styles["FieldValue"]),
            Paragraph("Permanent Address:", custom_styles["FieldLabel"]),
            Paragraph(employee.permanent_address or "—", custom_styles["FieldValue"]),
        ],
    ]
    contact_table = Table(contact_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(contact_table)
    elements.append(Spacer(1, 14))

    # Signatures block
    sig_data = [
        [
            Paragraph("<b>HR Verification:</b><br/><br/><br/>_______________________<br/>Authorized HR Officer", custom_styles["FieldValue"]),
            Paragraph("<b>Employee Confirmation:</b><br/><br/><br/>_______________________<br/>Employee Signature", custom_styles["FieldValue"]),
            Paragraph("<b>Date of Issue:</b><br/><br/><br/>_______________________<br/>Official Seal", custom_styles["FieldValue"]),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(KeepTogether(sig_table))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_joining_pdf(joining):
    """Generate official Dubai JOINING FORM PDF reproducing the exact form."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    custom_styles = get_base_styles()
    elements = []

    emp_name = joining.employee.full_name if joining.employee else ""

    # Title
    elements.append(Paragraph("JOINING FORM", custom_styles["JoiningTitle"]))
    elements.append(Spacer(1, 6))

    # Applicant details with Photo slot on the right
    # Left grid: 120mm, Right photo: 50mm
    app_rows = [
        [
            Paragraph("<b>Application Date:</b>", custom_styles["JoiningText"]),
            Paragraph(str(joining.application_date or "—"), custom_styles["JoiningText"]),
            Paragraph("<b>Joining Date:</b>", custom_styles["JoiningText"]),
            Paragraph(str(joining.joining_date or "—"), custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Name:</b>", custom_styles["JoiningText"]),
            Paragraph(emp_name or "—", custom_styles["JoiningBold"]),
            Paragraph("<b>Father Name:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.father_name or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Nationality:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.nationality or "—", custom_styles["JoiningText"]),
            Paragraph("<b>City:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.city or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Visa Status:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.visa_status or "—", custom_styles["JoiningText"]),
            Paragraph("<b>Visa Expire:</b>", custom_styles["JoiningText"]),
            Paragraph(str(joining.visa_expiry or "—"), custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Passport No:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.passport_number or "—", custom_styles["JoiningText"]),
            Paragraph("<b>Citizenship No:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.citizenship_number or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Passport Expiry:</b>", custom_styles["JoiningText"]),
            Paragraph(str(joining.passport_expiry or "—"), custom_styles["JoiningText"]),
            Paragraph("", custom_styles["JoiningText"]),
            Paragraph("", custom_styles["JoiningText"]),
        ],
    ]
    app_table = Table(app_rows, colWidths=[28 * mm, 37 * mm, 28 * mm, 37 * mm])
    app_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (1,0), (1,-1), 0.5, DARK_LINE),
        ('LINEBELOW', (3,0), (3,-2), 0.5, DARK_LINE),
    ]))

    photo_cell = [
        Paragraph("<font size=8 color='#888'>Passport Size<br/>Photo<br/>here</font>", ParagraphStyle('C', alignment=TA_CENTER))
    ]
    photo_table = Table([photo_cell], colWidths=[38 * mm], rowHeights=[44 * mm])
    photo_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, ACCENT),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    top_grid = Table([[app_table, photo_table]], colWidths=[140 * mm, 45 * mm])
    top_grid.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(top_grid)
    elements.append(Spacer(1, 6))

    # Phones Table
    phones_data = [
        [
            Paragraph("<b>Mobile No</b>", custom_styles["JoiningText"]),
            Paragraph(joining.mobile_number or "—", custom_styles["JoiningText"]),
            Paragraph("<b>2nd Mobile No</b>", custom_styles["JoiningText"]),
            Paragraph(joining.secondary_mobile_number or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>What's App</b>", custom_styles["JoiningText"]),
            Paragraph(joining.whatsapp_number or "—", custom_styles["JoiningText"]),
            Paragraph("<b>2nd What's App</b>", custom_styles["JoiningText"]),
            Paragraph(joining.secondary_whatsapp_number or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Home No</b>", custom_styles["JoiningText"]),
            Paragraph(joining.home_number or "—", custom_styles["JoiningText"]),
            Paragraph("<b>2nd Home No</b>", custom_styles["JoiningText"]),
            Paragraph(joining.secondary_home_number or "—", custom_styles["JoiningText"]),
        ],
    ]
    phones_table = Table(phones_data, colWidths=[38 * mm, 54 * mm, 38 * mm, 54 * mm])
    phones_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, DARK_LINE),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f0f0f0")),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#f0f0f0")),
    ]))
    elements.append(phones_table)
    elements.append(Spacer(1, 6))

    # Terms Section
    terms_data = [
        [
            Paragraph("<b>Basic Salary:</b>", custom_styles["JoiningText"]),
            Paragraph(f"{joining.basic_salary}" if joining.basic_salary else "—", custom_styles["JoiningText"]),
            Paragraph("<b>Commission (%):</b>", custom_styles["JoiningText"]),
            Paragraph(f"{joining.commission_percent}%" if joining.commission_percent else "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Allowance:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.allowance or "—", custom_styles["JoiningText"]),
            Paragraph("<b>Training Period:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.training_period or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Starting Date:</b>", custom_styles["JoiningText"]),
            Paragraph(str(joining.starting_date or "—"), custom_styles["JoiningText"]),
            Paragraph("<b>End Date:</b>", custom_styles["JoiningText"]),
            Paragraph(str(joining.end_date or "—"), custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Monthly Target:</b>", custom_styles["JoiningText"]),
            Paragraph(f"{joining.monthly_target}" if joining.monthly_target else "—", custom_styles["JoiningText"]),
            Paragraph("<b>Visa Charges:</b>", custom_styles["JoiningText"]),
            Paragraph(f"{joining.visa_charges}" if joining.visa_charges else "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>Job Title:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.job_title or (joining.employee.job_title if joining.employee else "—"), custom_styles["JoiningText"]),
            Paragraph("<b>HR Name:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.hr_name or "—", custom_styles["JoiningText"]),
        ],
        [
            Paragraph("<b>HR Phone:</b>", custom_styles["JoiningText"]),
            Paragraph(joining.hr_phone or "—", custom_styles["JoiningText"]),
            Paragraph("<b>EMP#</b>", custom_styles["JoiningText"]),
            Paragraph(f"<b>{joining.assigned_employee_number or (joining.employee.employee_id if joining.employee else '—')}</b>", custom_styles["JoiningText"]),
        ],
    ]
    terms_table = Table(terms_data, colWidths=[38 * mm, 54 * mm, 38 * mm, 54 * mm])
    terms_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('LINEBELOW', (1,0), (1,-1), 0.5, DARK_LINE),
        ('LINEBELOW', (3,0), (3,-1), 0.5, DARK_LINE),
    ]))
    elements.append(terms_table)
    elements.append(Spacer(1, 8))

    # Applicant Acknowledgment
    ack_text = """
    <b><font color="#1767bd">Applicant Acknowledgment:</font></b><br/>
    I. I am happy to confirm that all aspects have been fully clarified on our end and within the company.<br/>
    II. We are completely satisfied with the current alignment and ready to move forward.<br/>
    III. I have no further questions. Kindly close my file.
    """
    elements.append(Paragraph(ack_text, custom_styles["JoiningText"]))
    elements.append(Spacer(1, 14))

    # Signatures
    thumb_box = Table([[""]], colWidths=[28 * mm], rowHeights=[24 * mm])
    thumb_box.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.7, DARK_LINE)]))

    sig_grid = [
        [
            Paragraph("<b>Manager Signature:</b><br/><br/><br/>________________________", custom_styles["JoiningText"]),
            Paragraph("<b>Applicant Thumbprint:</b>", custom_styles["JoiningText"]),
            thumb_box,
            Paragraph("<b>Applicant Signature:</b><br/><br/><br/>________________________", custom_styles["JoiningText"]),
        ]
    ]
    sig_table = Table(sig_grid, colWidths=[55 * mm, 35 * mm, 32 * mm, 55 * mm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ]))
    elements.append(KeepTogether(sig_table))

    # Main outer border wrapper
    outer_table = Table([[elements]], colWidths=[185 * mm])
    outer_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.2, ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 6 * mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6 * mm),
        ('LEFTPADDING', (0,0), (-1,-1), 6 * mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 6 * mm),
    ]))

    full_doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )
    full_doc.build([outer_table])
    buffer.seek(0)
    return buffer.getvalue()


def generate_expense_pdf(expense):
    """Generate official Expense Bill / Payment Voucher PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    custom_styles = get_base_styles()
    elements = []

    # Header
    header_data = [
        [
            Paragraph("<b>OMS OPERATIONS</b><br/><font size=8 color='#666'>Finance & Accounts Department · Dubai, UAE</font>", styles["Normal"]),
            Paragraph(f"<b>PAYMENT VOUCHER</b><br/><font size=9 color='#173c32'>REF: {expense.reference_number}</font>", ParagraphStyle('R', alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=12, textColor=PRIMARY))
        ]
    ]
    header_table = Table(header_data, colWidths=[120 * mm, 60 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))

    # Summary Info
    emp_info = f"{expense.employee.full_name} ({expense.employee.employee_id})" if expense.employee else "—"
    dept_info = expense.department.name if expense.department else "—"
    info_data = [
        [
            Paragraph("<b>Payee / Vendor:</b>", custom_styles["FieldLabel"]),
            Paragraph(expense.vendor_name or "—", custom_styles["FieldValue"]),
            Paragraph("<b>Bill Date:</b>", custom_styles["FieldLabel"]),
            Paragraph(str(expense.bill_date), custom_styles["FieldValue"]),
        ],
        [
            Paragraph("<b>Employee:</b>", custom_styles["FieldLabel"]),
            Paragraph(emp_info, custom_styles["FieldValue"]),
            Paragraph("<b>Due Date:</b>", custom_styles["FieldLabel"]),
            Paragraph(str(expense.due_date) if expense.due_date else "—", custom_styles["FieldValue"]),
        ],
        [
            Paragraph("<b>Category:</b>", custom_styles["FieldLabel"]),
            Paragraph(expense.category or "—", custom_styles["FieldValue"]),
            Paragraph("<b>Payment Status:</b>", custom_styles["FieldLabel"]),
            Paragraph(expense.get_status_display(), custom_styles["FieldValue"]),
        ],
        [
            Paragraph("<b>Payment Method:</b>", custom_styles["FieldLabel"]),
            Paragraph(expense.get_payment_method_display(), custom_styles["FieldValue"]),
            Paragraph("<b>Invoice #:</b>", custom_styles["FieldLabel"]),
            Paragraph(expense.invoice_number or "—", custom_styles["FieldValue"]),
        ],
    ]
    info_table = Table(info_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # Line items
    elements.append(Paragraph("<b>ITEMIZED EXPENSE BREAKDOWN</b>", custom_styles["SectionHeader"]))
    items = list(expense.items.all())
    if items:
        table_rows = [
            [
                Paragraph("<b>Item / Product</b>", custom_styles["TableHead"]),
                Paragraph("<b>Qty</b>", custom_styles["TableHead"]),
                Paragraph("<b>Unit Price</b>", custom_styles["TableHead"]),
                Paragraph("<b>Total</b>", custom_styles["TableHead"]),
            ]
        ]
        for item in items:
            table_rows.append([
                Paragraph(item.product_name, custom_styles["TableCell"]),
                Paragraph(f"{item.quantity:,.2f}", custom_styles["TableCell"]),
                Paragraph(f"{expense.currency} {item.unit_price:,.2f}", custom_styles["TableCell"]),
                Paragraph(f"{expense.currency} {item.line_total:,.2f}", custom_styles["TableCell"]),
            ])
        table_rows.append([
            Paragraph("<b>TOTAL AMOUNT:</b>", custom_styles["TableCell"]),
            Paragraph("", custom_styles["TableCell"]),
            Paragraph("", custom_styles["TableCell"]),
            Paragraph(f"<b>{expense.currency} {expense.amount:,.2f}</b>", custom_styles["TableCell"]),
        ])
        items_table = Table(table_rows, colWidths=[80 * mm, 25 * mm, 35 * mm, 40 * mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY),
            ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e8f0eb")),
        ]))
        elements.append(items_table)
    else:
        desc_data = [
            [Paragraph("<b>Description:</b>", custom_styles["FieldLabel"]), Paragraph(expense.description or "General Expense", custom_styles["FieldValue"])],
            [Paragraph("<b>Total Amount:</b>", custom_styles["FieldLabel"]), Paragraph(f"<b>{expense.currency} {expense.amount:,.2f}</b>", custom_styles["FieldValue"])],
        ]
        desc_table = Table(desc_data, colWidths=[40 * mm, 140 * mm])
        desc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(desc_table)

    if expense.notes:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Notes:</b> {expense.notes}", custom_styles["FieldValue"]))

    elements.append(Spacer(1, 20))

    # Approvals section
    approver = expense.approved_by.get_full_name() or expense.approved_by.username if expense.approved_by else "Pending"
    app_date = str(expense.approved_at.date()) if expense.approved_at else "—"
    sig_data = [
        [
            Paragraph("<b>Prepared By:</b><br/><br/><br/>_______________________<br/>Accounts Officer", custom_styles["FieldValue"]),
            Paragraph(f"<b>Approved By:</b><br/>{approver}<br/>Date: {app_date}<br/>_______________________<br/>Manager / Finance Head", custom_styles["FieldValue"]),
            Paragraph("<b>Received By:</b><br/><br/><br/>_______________________<br/>Payee Signature", custom_styles["FieldValue"]),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(KeepTogether(sig_table))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_expense_report_pdf(queryset, title="Expense & Financial Report", date_range=""):
    """Generate Expense Summary Report PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    custom_styles = get_base_styles()
    elements = []

    # Header
    elements.append(Paragraph(f"<b>{title.upper()}</b>", custom_styles["DocTitle"]))
    elements.append(Paragraph(f"Generated: {date_range or 'All Records'} · OMS Financial Management", custom_styles["DocSubtitle"]))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=6, spaceAfter=10))

    total_amount = sum(e.amount for e in queryset)

    table_rows = [
        [
            Paragraph("<b>REF #</b>", custom_styles["TableHead"]),
            Paragraph("<b>DATE</b>", custom_styles["TableHead"]),
            Paragraph("<b>VENDOR / EMPLOYEE</b>", custom_styles["TableHead"]),
            Paragraph("<b>CATEGORY</b>", custom_styles["TableHead"]),
            Paragraph("<b>STATUS</b>", custom_styles["TableHead"]),
            Paragraph("<b>AMOUNT</b>", custom_styles["TableHead"]),
        ]
    ]
    for exp in queryset:
        party = exp.vendor_name or (exp.employee.full_name if exp.employee else "—")
        table_rows.append([
            Paragraph(exp.reference_number, custom_styles["TableCell"]),
            Paragraph(str(exp.bill_date), custom_styles["TableCell"]),
            Paragraph(party[:28], custom_styles["TableCell"]),
            Paragraph((exp.category or "—")[:20], custom_styles["TableCell"]),
            Paragraph(exp.get_status_display(), custom_styles["TableCell"]),
            Paragraph(f"{exp.currency} {exp.amount:,.2f}", custom_styles["TableCell"]),
        ])

    table_rows.append([
        Paragraph("<b>TOTAL</b>", custom_styles["TableCell"]),
        Paragraph("", custom_styles["TableCell"]),
        Paragraph(f"{queryset.count()} records", custom_styles["TableCell"]),
        Paragraph("", custom_styles["TableCell"]),
        Paragraph("", custom_styles["TableCell"]),
        Paragraph(f"<b>AED {total_amount:,.2f}</b>", custom_styles["TableCell"]),
    ])

    report_table = Table(table_rows, colWidths=[28 * mm, 24 * mm, 50 * mm, 36 * mm, 26 * mm, 22 * mm])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e8f0eb")),
    ]))
    elements.append(report_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_employee_report_pdf(queryset, title="Employee Directory Report"):
    """Generate Employee Directory Report PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    custom_styles = get_base_styles()
    elements = []

    elements.append(Paragraph(f"<b>{title.upper()}</b>", custom_styles["DocTitle"]))
    elements.append(Paragraph(f"Total Records: {queryset.count()} · OMS People Operations", custom_styles["DocSubtitle"]))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=6, spaceAfter=10))

    table_rows = [
        [
            Paragraph("<b>EMP ID</b>", custom_styles["TableHead"]),
            Paragraph("<b>FULL NAME</b>", custom_styles["TableHead"]),
            Paragraph("<b>PHONE</b>", custom_styles["TableHead"]),
            Paragraph("<b>DEPARTMENT</b>", custom_styles["TableHead"]),
            Paragraph("<b>DESIGNATION</b>", custom_styles["TableHead"]),
            Paragraph("<b>STATUS</b>", custom_styles["TableHead"]),
        ]
    ]
    for emp in queryset:
        dept = emp.department.name if emp.department else "—"
        desig = emp.designation.name if emp.designation else (emp.job_title or "—")
        table_rows.append([
            Paragraph(emp.employee_id, custom_styles["TableCell"]),
            Paragraph(emp.full_name, custom_styles["TableCell"]),
            Paragraph(emp.phone, custom_styles["TableCell"]),
            Paragraph(dept[:20], custom_styles["TableCell"]),
            Paragraph(desig[:22], custom_styles["TableCell"]),
            Paragraph(emp.get_status_display(), custom_styles["TableCell"]),
        ])

    emp_table = Table(table_rows, colWidths=[26 * mm, 46 * mm, 32 * mm, 34 * mm, 30 * mm, 18 * mm])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(emp_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
