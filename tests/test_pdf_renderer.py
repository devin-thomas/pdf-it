from io import BytesIO

from pypdf import PdfReader

from pdf_it.pdf_renderer import render_document
from pdf_it.schemas import DocumentBlock, DocumentPlan, DocumentSection


def test_pdf_is_valid_searchable_and_escapes_markup() -> None:
    plan = DocumentPlan(
        title="Research & Results <2026>",
        subtitle="A readable, generated report",
        summary="This summary explains the result without inventing evidence.",
        sections=[
            DocumentSection(
                heading="Evidence",
                blocks=[
                    DocumentBlock(
                        kind="paragraph",
                        text=(
                            "Literal tags like <b>source text</b> stay literal"
                            " and searchable."
                        ),
                    ),
                    DocumentBlock(
                        kind="code",
                        text=(
                            "def keep_literal(value):\n"
                            "    if value < 10:\n"
                            "        return value"
                        ),
                    ),
                ],
                callout="Keep the strongest supported conclusion in view.",
            ),
            DocumentSection(
                heading="Next steps",
                blocks=[
                    DocumentBlock(
                        kind="paragraph",
                        text="Validate the conclusion with the original material.",
                    )
                ],
            ),
        ],
    )

    payload = render_document(plan)
    reader = PdfReader(BytesIO(payload))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert payload.startswith(b"%PDF-")
    assert reader.metadata.title == plan.title
    assert reader.metadata.author == "pdf-it"
    assert "Research & Results <2026>" in text
    assert "<b>source text</b>" in text
    assert "def keep_literal(value):" in text
    assert "return value" in text
    assert "Next steps" in text
    assert b"Courier" in payload
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
            DocumentSection(
                heading="Detailed analysis",
                blocks=[
                    DocumentBlock(kind="paragraph", text=paragraph)
                    for paragraph in paragraphs[:8]
                ],
            )
            for _ in range(3)
        ],
    )

    reader = PdfReader(BytesIO(render_document(plan)))
    assert len(reader.pages) >= 3
    assert "PDF-IT" in (reader.pages[-1].extract_text() or "")
