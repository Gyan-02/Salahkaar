from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


OUTPUT = "output/pdf/pm_kisan_synthetic_demo_documents.pdf"
WIDTH, HEIGHT = A4

INK = colors.HexColor("#163B37")
GREEN = colors.HexColor("#1E675C")
PALE = colors.HexColor("#E8F1EC")
GOLD = colors.HexColor("#C4A84D")
MUTED = colors.HexColor("#58706B")
LINE = colors.HexColor("#C9D7D1")
PAPER = colors.HexColor("#FCFCF8")
RED = colors.HexColor("#A33D35")


def rounded_box(c, x, y, w, h, fill=colors.white, stroke=LINE, radius=4 * mm):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def watermark(c):
    c.saveState()
    c.translate(WIDTH / 2, HEIGHT / 2)
    c.rotate(32)
    c.setFillColor(colors.Color(0.64, 0.20, 0.17, alpha=0.09))
    c.setFont("Helvetica-Bold", 31)
    text = "SYNTHETIC DEMO - NOT VALID"
    c.drawCentredString(0, 0, text)
    c.restoreState()


def header(c, title, subtitle, page_number):
    c.setFillColor(PAPER)
    c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    c.setFillColor(INK)
    c.rect(0, HEIGHT - 38 * mm, WIDTH, 38 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.roundRect(18 * mm, HEIGHT - 20 * mm, 43 * mm, 8 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(39.5 * mm, HEIGHT - 17.3 * mm, "SOFTWARE TEST DOCUMENT")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 21)
    c.drawString(18 * mm, HEIGHT - 29 * mm, title)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#C8D8D4"))
    c.drawString(18 * mm, HEIGHT - 34.2 * mm, subtitle)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(WIDTH - 18 * mm, 11 * mm, f"Synthetic PM-KISAN demo | Page {page_number} of 2")
    c.setStrokeColor(LINE)
    c.line(18 * mm, 15 * mm, WIDTH - 18 * mm, 15 * mm)


def field(c, x, y, w, label, value, height=22 * mm):
    rounded_box(c, x, y, w, height)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 5 * mm, y + height - 7 * mm, label.upper())
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    max_width = w - 10 * mm
    size = 12
    while stringWidth(value, "Helvetica-Bold", size) > max_width and size > 8:
        size -= 0.5
    c.setFont("Helvetica-Bold", size)
    c.drawString(x + 5 * mm, y + 7 * mm, value)


def warning(c, y):
    rounded_box(c, 18 * mm, y, WIDTH - 36 * mm, 20 * mm, fill=colors.HexColor("#F9ECEA"), stroke=colors.HexColor("#E5BBB5"))
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(24 * mm, y + 12 * mm, "SYNTHETIC DEMO - NOT VALID")
    c.setFont("Helvetica", 8)
    c.drawString(24 * mm, y + 7 * mm, "Created only for software demonstration and OCR testing. Not issued by any authority.")


def identity_page(c):
    header(c, "IDENTITY RECORD", "Fictional applicant identity details for extraction testing", 1)
    warning(c, HEIGHT - 66 * mm)

    rounded_box(c, 18 * mm, HEIGHT - 123 * mm, 52 * mm, 47 * mm, fill=PALE)
    c.setFillColor(GREEN)
    c.circle(44 * mm, HEIGHT - 93 * mm, 8 * mm, fill=1, stroke=0)
    c.roundRect(31 * mm, HEIGHT - 115 * mm, 26 * mm, 16 * mm, 7 * mm, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(44 * mm, HEIGHT - 120 * mm, "SYNTHETIC PROFILE")

    field(c, 77 * mm, HEIGHT - 99 * mm, WIDTH - 95 * mm, "Name", "Ravi Kumar")
    field(c, 77 * mm, HEIGHT - 123 * mm, WIDTH - 95 * mm, "Date of Birth", "12/04/1985")

    rounded_box(c, 18 * mm, HEIGHT - 177 * mm, WIDTH - 36 * mm, 44 * mm)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(23 * mm, HEIGHT - 142 * mm, "ADDRESS")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(23 * mm, HEIGHT - 153 * mm, "House 42, Demo Colony")
    c.setFont("Helvetica", 11)
    c.drawString(23 * mm, HEIGHT - 163 * mm, "Patna, Bihar 800001")

    rounded_box(c, 18 * mm, HEIGHT - 215 * mm, WIDTH - 36 * mm, 27 * mm, fill=PALE)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(23 * mm, HEIGHT - 198 * mm, "DOCUMENT PURPOSE")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.5)
    text = "Use this page to demonstrate structured extraction of name, date of birth, and address. It is not an Aadhaar card or an official identity document."
    note = Paragraph(
        text,
        ParagraphStyle(
            "note", fontName="Helvetica", fontSize=8.5, leading=11, textColor=MUTED
        ),
    )
    note.wrapOn(c, WIDTH - 48 * mm, 18 * mm)
    note.drawOn(c, 23 * mm, HEIGHT - 211 * mm)
    watermark(c)
    c.showPage()


def land_page(c):
    header(c, "LAND RECORD EXTRACT", "Fictional cultivable-land record for extraction testing", 2)
    warning(c, HEIGHT - 66 * mm)

    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(18 * mm, HEIGHT - 81 * mm, "PRIMARY RECORD DETAILS")

    gap = 6 * mm
    col = (WIDTH - 36 * mm - gap) / 2
    field(c, 18 * mm, HEIGHT - 108 * mm, col, "Owner Name", "Ravi Kumar")
    field(c, 18 * mm + col + gap, HEIGHT - 108 * mm, col, "Plot Identifier", "DEMO-PL-042")
    field(c, 18 * mm, HEIGHT - 136 * mm, col, "Ownership Date", "01/10/2018")
    field(c, 18 * mm + col + gap, HEIGHT - 136 * mm, col, "Land Type", "Cultivable agricultural land")

    rounded_box(c, 18 * mm, HEIGHT - 181 * mm, WIDTH - 36 * mm, 35 * mm)
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(23 * mm, HEIGHT - 155 * mm, "ADDRESS")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(23 * mm, HEIGHT - 166 * mm, "House 42, Demo Colony, Patna, Bihar 800001")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(23 * mm, HEIGHT - 175 * mm, "District: Patna   |   State: Bihar   |   Record status: Synthetic demonstration record")

    rounded_box(c, 18 * mm, HEIGHT - 222 * mm, WIDTH - 36 * mm, 30 * mm, fill=PALE)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(23 * mm, HEIGHT - 202 * mm, "EXTRACTION NOTE")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(23 * mm, HEIGHT - 212 * mm, "The owner name and address intentionally match the synthetic identity record on page 1.")
    c.drawString(23 * mm, HEIGHT - 218 * mm, "The ownership date is demonstration data and is not used as an active eligibility rule.")
    watermark(c)
    c.showPage()


def main():
    c = canvas.Canvas(OUTPUT, pagesize=A4, pageCompression=1)
    c.setTitle("PM-KISAN Synthetic Demo Documents")
    c.setAuthor("Salahkaar Demo")
    c.setSubject("Synthetic OCR testing documents - not valid")
    identity_page(c)
    land_page(c)
    c.save()


if __name__ == "__main__":
    main()
