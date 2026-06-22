from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


OUT = Path("output/pdf")
W, H = A4
INK = colors.HexColor("#163B37")
GREEN = colors.HexColor("#1E675C")
PALE = colors.HexColor("#E8F1EC")
GOLD = colors.HexColor("#C4A84D")
MUTED = colors.HexColor("#58706B")
LINE = colors.HexColor("#C9D7D1")
PAPER = colors.HexColor("#FCFCF8")
RED = colors.HexColor("#A33D35")


def box(c, x, y, width, height, fill=colors.white, stroke=LINE):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, width, height, 4 * mm, fill=1, stroke=1)


def watermark(c):
    c.saveState()
    c.translate(W / 2, H / 2)
    c.rotate(32)
    c.setFillColor(colors.Color(0.64, 0.20, 0.17, alpha=0.09))
    c.setFont("Helvetica-Bold", 31)
    c.drawCentredString(0, 0, "SYNTHETIC DEMO - NOT VALID")
    c.restoreState()


def start(c, title, subtitle, program):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(INK)
    c.rect(0, H - 38 * mm, W, 38 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.roundRect(18 * mm, H - 20 * mm, 47 * mm, 8 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 7.4)
    c.drawCentredString(41.5 * mm, H - 17.3 * mm, "SOFTWARE TEST DOCUMENT")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(18 * mm, H - 29 * mm, title)
    c.setFillColor(colors.HexColor("#C8D8D4"))
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, H - 34.2 * mm, subtitle)

    box(c, 18 * mm, H - 66 * mm, W - 36 * mm, 20 * mm,
        fill=colors.HexColor("#F9ECEA"), stroke=colors.HexColor("#E5BBB5"))
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(24 * mm, H - 54 * mm, "SYNTHETIC DEMO - NOT VALID")
    c.setFont("Helvetica", 8)
    c.drawString(24 * mm, H - 59 * mm,
                 "Created only for software demonstration and OCR testing. Not issued by any authority.")

    c.setStrokeColor(LINE)
    c.line(18 * mm, 15 * mm, W - 18 * mm, 15 * mm)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W - 18 * mm, 11 * mm, f"{program} synthetic demo document")


def field(c, x, y, width, label, value, height=24 * mm, value_size=12):
    box(c, x, y, width, height)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 5 * mm, y + height - 7 * mm, label.upper())
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", value_size)
    c.drawString(x + 5 * mm, y + 7 * mm, value)


def note(c, heading, lines):
    height = 24 * mm + max(0, len(lines) - 1) * 6 * mm
    y = 38 * mm
    box(c, 18 * mm, y, W - 36 * mm, height, fill=PALE)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(23 * mm, y + height - 9 * mm, heading)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.2)
    for index, line in enumerate(lines):
        c.drawString(23 * mm, y + height - (17 + index * 6) * mm, line)


def finish(c):
    watermark(c)
    c.showPage()
    c.save()


def identity():
    path = OUT / "nmmss_synthetic_identity_record.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("NMMSS Synthetic Identity Record")
    start(c, "IDENTITY RECORD", "Fictional student identity details for extraction testing", "NMMSS")
    field(c, 18 * mm, H - 103 * mm, W - 36 * mm, "Student Name", "Asha Devi")
    field(c, 18 * mm, H - 134 * mm, W - 36 * mm, "Date of Birth", "06/04/2012")
    field(c, 18 * mm, H - 177 * mm, W - 36 * mm, "Address",
          "House 18, Shiksha Nagar, Patna, Bihar 800014", height=33 * mm, value_size=11)
    note(c, "DOCUMENT PURPOSE", [
        "Use for extracting the student's name, date of birth, and address.",
        "This is not an Aadhaar card or an official identity document.",
    ])
    finish(c)
    return path


def bank():
    path = OUT / "nmmss_synthetic_bank_passbook.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("NMMSS Synthetic Bank Passbook")
    start(c, "BANK PASSBOOK RECORD", "Fictional student bank details for extraction testing", "NMMSS")
    field(c, 18 * mm, H - 103 * mm, W - 36 * mm, "Account Holder Name", "Asha Devi")
    field(c, 18 * mm, H - 134 * mm, W - 36 * mm, "IFSC", "DEMO0001234")
    field(c, 18 * mm, H - 165 * mm, W - 36 * mm, "Bank Type", "Synthetic scheduled-bank record")
    note(c, "DOCUMENT PURPOSE", [
        "Use for extracting the account-holder name and IFSC field.",
        "No real bank account exists and this record cannot be used for a transaction.",
    ])
    finish(c)
    return path


def income():
    path = OUT / "nmmss_synthetic_income_certificate.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("NMMSS Synthetic Income Certificate")
    start(c, "INCOME CERTIFICATE", "Fictional parental-income details for extraction testing", "NMMSS")
    field(c, 18 * mm, H - 103 * mm, W - 36 * mm, "Student Name", "Asha Devi")
    field(c, 18 * mm, H - 134 * mm, W - 36 * mm, "Annual Income", "INR 300000")
    gap = 6 * mm
    col = (W - 36 * mm - gap) / 2
    field(c, 18 * mm, H - 165 * mm, col, "Issue Date", "01/06/2026")
    field(c, 18 * mm + col + gap, H - 165 * mm, col, "Expiry Date", "31/05/2027")
    note(c, "DOCUMENT PURPOSE", [
        "Use for extracting the student's name, annual income, issue date, and expiry date.",
        "The amount and dates are fictional demonstration values.",
    ])
    finish(c)
    return path


def family():
    path = OUT / "pmjay_synthetic_family_record.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    c.setTitle("PM-JAY Synthetic Family Record")
    start(c, "FAMILY RECORD", "Fictional household composition for extraction testing", "PM-JAY")

    box(c, 18 * mm, H - 145 * mm, W - 36 * mm, 68 * mm)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(23 * mm, H - 87 * mm, "FAMILY MEMBERS")
    members = [("01", "Meera Devi"), ("02", "Arun Kumar"), ("03", "Kiran Kumar")]
    for index, (number, name) in enumerate(members):
        y = H - (103 + index * 15) * mm
        c.setFillColor(PALE)
        c.circle(27 * mm, y + 2 * mm, 5 * mm, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(27 * mm, y, number)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(38 * mm, y, name)

    field(c, 18 * mm, H - 187 * mm, W - 36 * mm, "Household Address",
          "House 27, Seva Colony, Patna, Bihar 800020", height=32 * mm, value_size=11)
    note(c, "POLICY NOTICE", [
        "This page is only an extraction fixture for family-members and address fields.",
        "It does not establish PM-JAY eligibility. Official Bihar criteria remain pending in the demo.",
    ])
    finish(c)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for generated in (identity(), bank(), income(), family()):
        print(generated)


if __name__ == "__main__":
    main()
