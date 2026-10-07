from pathlib import Path

from pypdf import PdfReader

from app.services.certificate_generator import generate_certificate_pdf


def test_generates_readable_certificate_pdf(tmp_path: Path):
    output_path = tmp_path / "nested" / "certificate.pdf"

    result = generate_certificate_pdf(
        recipient_name="Avery Example",
        event_name="Practical Python Workshop",
        event_date="2026-10-07",
        issuer_name="Example Academy",
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.read_bytes().startswith(b"%PDF")
    page_text = PdfReader(str(output_path)).pages[0].extract_text()
    assert "Avery Example" in page_text
    assert "Practical Python Workshop" in page_text