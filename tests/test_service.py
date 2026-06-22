from io import BytesIO

from pypdf import PdfReader

from pdf_it.config import Provider
from pdf_it.ingestion import PreparedSources, SourceUpload
from pdf_it.providers import ProviderRequestError
from pdf_it.schemas import DocumentBlock, DocumentPlan, DocumentSection
from pdf_it.service import create_document_plan, create_pdf_from_sources, create_pdf_from_text


def sample_plan() -> DocumentPlan:
    return DocumentPlan(
        title="A Clear Document",
        subtitle="A useful subtitle",
        summary="The central idea in one short paragraph.",
        sections=[
            DocumentSection(
                heading="First section",
                blocks=[
                    DocumentBlock(
                        kind="paragraph",
                        text="A preserved fact and its explanation.",
                    )
                ],
                callout="The important point.",
            )
        ],
    )


class FakeStructuredModel:
    def __init__(self, result: DocumentPlan) -> None:
        self.result = result
        self.schema = None
        self.messages = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, messages):
        self.messages = messages
        return self.result


class FailingStructuredModel:
    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        raise ProviderRequestError("provider unavailable")


def test_document_plan_uses_schema_and_data_boundaries() -> None:
    model = FakeStructuredModel(sample_plan())
    result = create_document_plan("Source fact", "Write for experts", model)

    assert result.title == "A Clear Document"
    assert model.schema is DocumentPlan
    assert "<SOURCE>\nSource fact\n</SOURCE>" in model.messages[1].content
    assert "<CREATIVE_DIRECTION>" in model.messages[1].content


def test_end_to_end_service_with_injected_model() -> None:
    model = FakeStructuredModel(sample_plan())
    pdf, plan = create_pdf_from_text(
        "Source fact",
        "Uploaded context",
        "Be concise",
        Provider.GEMINI,
        "unused-because-model-is-injected",
        model=model,
    )
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1_000
    assert plan.title == "A Clear Document"


def test_mixed_source_service_path_with_injected_model() -> None:
    model = FakeStructuredModel(sample_plan())
    pdf, plan, prepared = create_pdf_from_sources(
        "Typed fact",
        [SourceUpload(name="notes.md", data=b"# Heading\n\nExtra detail")],
        [],
        "Be concise",
        Provider.GEMINI,
        "unused-because-model-is-injected",
        "gemini-3.5-flash",
        model=model,
    )

    assert pdf.startswith(b"%PDF-")
    assert plan.title == "A Clear Document"
    assert prepared.source_count == 2
    assert "[Source: notes.md]" in model.messages[1].content


def test_youtube_transcript_falls_back_to_source_preserving_pdf(
    monkeypatch,
) -> None:
    transcript = "A unique transcript phrase that must remain in the generated PDF."
    monkeypatch.setattr(
        "pdf_it.service.prepare_source_text",
        lambda *args, **kwargs: PreparedSources(
            source=f"[Source: YouTube transcript 1]\n{transcript}",
            source_count=1,
        ),
    )

    pdf, plan, prepared = create_pdf_from_sources(
        "",
        [],
        ["https://youtu.be/e-GR3PlEOVU"],
        "",
        Provider.GEMINI,
        "provider-key",
        "gemini-3.1-flash-lite",
        model=FailingStructuredModel(),
    )

    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
    assert pdf.startswith(b"%PDF-")
    assert plan.title == "YouTube Transcript"
    assert "e-GR3PlEOVU" in (plan.subtitle or "")
    assert transcript in extracted
    assert prepared.used_local_plan


def test_youtube_transcript_without_api_key_uses_local_plan(monkeypatch) -> None:
    monkeypatch.setattr(
        "pdf_it.service.prepare_source_text",
        lambda *args, **kwargs: PreparedSources(
            source="[Source: YouTube transcript 1]\nCaption text",
            source_count=1,
        ),
    )
    monkeypatch.setattr(
        "pdf_it.service.build_chat_model",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("provider should not run")
        ),
    )

    pdf, _, prepared = create_pdf_from_sources(
        "",
        [],
        ["e-GR3PlEOVU"],
        "",
        Provider.GEMINI,
        "",
        "gemini-3.1-flash-lite",
    )

    assert pdf.startswith(b"%PDF-")
    assert prepared.used_local_plan
