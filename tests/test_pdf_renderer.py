from io import BytesIO

from pypdf import PdfReader

from typeset.pdf_renderer import render_document
from typeset.schemas import DocumentPlan, DocumentSection


def test_pdf_is_valid_searchable_and_escapes_markup() -> None:
    plan = DocumentPlan(
        title="Research & Results <2026>",
        subtitle="A readable, generated report",
        summary="This summary explains the result without inventing evidence.",
        sections=[
            DocumentSection(
                heading="Evidence",
                paragraphs=[
                    "Literal tags like <b>source text</b> stay literal and searchable."
                ],
                callout="Keep the strongest supported conclusion in view.",
            ),
            DocumentSection(
                heading="Next steps",
                paragraphs=["Validate the conclusion with the original material."],
            ),
        ],
    )

    payload = render_document(plan)
    reader = PdfReader(BytesIO(payload))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert payload.startswith(b"%PDF-")
    assert reader.metadata.title == plan.title
    assert "Research & Results <2026>" in text
    assert "<b>source text</b>" in text
    assert "Next steps" in text
    assert all(
        (page.mediabox.width, page.mediabox.height) == (595.2756, 841.8898)
        for page in reader.pages
    )


def test_long_document_paginates_with_page_labels() -> None:
    paragraphs = [
        f"Paragraph {number}. " + ("Readable source material. " * 18)
        for number in range(22)
    ]
    plan = DocumentPlan(
        title="Long-form report",
        sections=[
            DocumentSection(heading="Detailed analysis", paragraphs=paragraphs[:8])
            for _ in range(3)
        ],
    )

    reader = PdfReader(BytesIO(render_document(plan)))
    assert len(reader.pages) >= 3
    assert "TYPESET" in (reader.pages[-1].extract_text() or "")
