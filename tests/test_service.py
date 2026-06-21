from pdf_it.config import Provider
from pdf_it.ingestion import SourceUpload
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
