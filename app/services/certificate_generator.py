from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def generate_certificate_pdf(
    *,
    recipient_name: str,
    event_name: str,
    event_date: str,
    issuer_name: str,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = landscape(letter)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    margin = 0.48 * inch
    pdf.setStrokeColor(colors.HexColor("#173F35"))
    pdf.setLineWidth(3)
    pdf.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)
    pdf.setStrokeColor(colors.HexColor("#B58A45"))
    pdf.setLineWidth(1)
    pdf.rect(margin + 10, margin + 10, page_width - 2 * (margin + 10), page_height - 2 * (margin + 10))

    pdf.setFillColor(colors.HexColor("#173F35"))
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(page_width / 2, page_height - 1.35 * inch, "CERTIFICATE OF ACHIEVEMENT")
    pdf.setFillColor(colors.HexColor("#4D5A54"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(page_width / 2, page_height - 2.05 * inch, "This certificate is proudly presented to")

    pdf.setFillColor(colors.HexColor("#173F35"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(page_width / 2, page_height - 2.85 * inch, recipient_name)
    pdf.setStrokeColor(colors.HexColor("#B58A45"))
    pdf.line(page_width * 0.25, page_height - 3.05 * inch, page_width * 0.75, page_height - 3.05 * inch)

    pdf.setFillColor(colors.HexColor("#4D5A54"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(page_width / 2, page_height - 3.55 * inch, "for successful participation in")
    pdf.setFillColor(colors.HexColor("#252D29"))
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawCentredString(page_width / 2, page_height - 4.0 * inch, event_name)

    pdf.setFillColor(colors.HexColor("#4D5A54"))
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(page_width / 2, 1.22 * inch, f"{event_date}  |  Presented by {issuer_name}")
    pdf.setStrokeColor(colors.HexColor("#173F35"))
    pdf.line(page_width * 0.39, 0.92 * inch, page_width * 0.61, 0.92 * inch)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(page_width / 2, 0.72 * inch, issuer_name)

    pdf.save()
    return output_path