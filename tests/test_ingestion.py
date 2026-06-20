import io

import pytest
from docx import Document
from reportlab.pdfgen import canvas

from pdf_it.config import MAX_SOURCE_CHARACTERS, Provider
from pdf_it.ingestion import (
    SourceUpload,
    extract_upload_text,
    fetch_youtube_transcript,
    prepare_source_text,
)
from pdf_it.validation import InputValidationError


def render_pdf_bytes(*lines: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    height = 780
    for line in lines:
        pdf.drawString(72, height, line)
        height -= 18
    pdf.save()
    return buffer.getvalue()


def render_docx_bytes(*paragraphs: str) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_prepare_source_text_combines_typed_and_uploaded_sources() -> None:
    prepared = prepare_source_text(
        "Typed source",
        [SourceUpload(name="notes.md", data=b"# Heading\n\nBody text")],
        [],
        Provider.GEMINI,
        "unit-test-key",
        "gemini-3.5-flash",
    )

    assert prepared.source_count == 2
    assert "[Source: Free text]" in prepared.source
    assert "[Source: notes.md]" in prepared.source
    assert "Heading" in prepared.source


def test_prepare_source_text_truncates_large_mixed_inputs() -> None:
    large_text = "A" * MAX_SOURCE_CHARACTERS
    prepared = prepare_source_text(
        large_text,
        [SourceUpload(name="snippet.py", data=b"print('hello')\n" * 2000)],
        [],
        Provider.GEMINI,
        "unit-test-key",
        "gemini-3.5-flash",
    )

    assert len(prepared.source) <= MAX_SOURCE_CHARACTERS
    assert "[Truncated to fit the shared source limit.]" in prepared.source


def test_extract_upload_text_supports_csv_via_dataframe_rendering() -> None:
    csv_bytes = b"name,score\nAva,9\nNoah,7\n"

    result = extract_upload_text(
        SourceUpload(name="scores.csv", data=csv_bytes),
        Provider.GEMINI,
        "unit-test-key",
        "gemini-3.5-flash",
    )

    assert "Rows: 2, Columns: 2" in result
    assert "Ava" in result


def test_extract_upload_text_supports_pdf_via_pypdf() -> None:
    result = extract_upload_text(
        SourceUpload(
            name="brief.pdf",
            data=render_pdf_bytes("Quarterly summary", "Revenue up"),
        ),
        Provider.GEMINI,
        "unit-test-key",
        "gemini-3.5-flash",
    )

    assert "Quarterly summary" in result
    assert "Revenue up" in result


def test_extract_upload_text_supports_docx_via_python_docx() -> None:
    result = extract_upload_text(
        SourceUpload(
            name="brief.docx",
            data=render_docx_bytes("First paragraph", "Second note"),
        ),
        Provider.GEMINI,
        "unit-test-key",
        "gemini-3.5-flash",
    )

    assert "First paragraph" in result
    assert "Second note" in result


def test_extract_upload_text_rejects_legacy_doc_without_optional_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("pdf_it.ingestion.load_udoc", lambda: None)

    with pytest.raises(InputValidationError, match="Save it as `.docx` or `.pdf`"):
        extract_upload_text(
            SourceUpload(name="legacy.doc", data=b"placeholder"),
            Provider.GEMINI,
            "unit-test-key",
            "gemini-3.5-flash",
        )


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("tool.scala", "Copy the file contents"),
        ("clip.mov", "Upload a transcript"),
    ],
)
def test_extract_upload_text_suggests_next_steps_for_unsupported_extensions(
    name: str,
    message: str,
) -> None:
    with pytest.raises(InputValidationError, match=message):
        extract_upload_text(
            SourceUpload(name=name, data=b"placeholder"),
            Provider.GEMINI,
            "unit-test-key",
            "gemini-3.5-flash",
        )


def test_claude_audio_uploads_require_a_supported_transcription_provider() -> None:
    with pytest.raises(InputValidationError, match="Gemini or OpenAI"):
        extract_upload_text(
            SourceUpload(name="call.mp3", data=b"audio-bytes"),
            Provider.ANTHROPIC,
            "unit-test-key",
            "claude-sonnet-4-6",
        )


def test_fetch_youtube_transcript_uses_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTranscript:
        def to_raw_data(self) -> list[dict[str, str]]:
            return [{"text": "First line"}, {"text": "Second line"}]

    class FakeApi:
        def fetch(self, video_id: str, languages) -> FakeTranscript:
            assert video_id == "abc123"
            return FakeTranscript()

    monkeypatch.setattr("pdf_it.ingestion.YouTubeTranscriptApi", lambda: FakeApi())
    result = fetch_youtube_transcript("https://www.youtube.com/watch?v=abc123")

    assert result == "First line\nSecond line"


def test_prepare_source_text_limits_uploaded_file_count() -> None:
    uploads = [SourceUpload(name=f"file-{index}.txt", data=b"hello") for index in range(6)]

    with pytest.raises(InputValidationError, match="at most 5"):
        prepare_source_text(
            "",
            uploads,
            [],
            Provider.GEMINI,
            "unit-test-key",
            "gemini-3.5-flash",
        )
