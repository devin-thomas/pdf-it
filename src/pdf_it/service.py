"""Orchestration boundary between user input, LangChain, and PDF rendering."""

from collections.abc import Callable, Sequence

from langchain_core.language_models.chat_models import BaseChatModel

from .config import Provider
from .ingestion import PreparedSources, SourceUpload, prepare_source_text
from .pdf_renderer import render_document
from .prompts import build_messages
from .providers import build_chat_model, safe_provider_error
from .schemas import DocumentPlan
from .validation import combine_source_text, validate_instructions

ProgressReporter = Callable[[str, int], None]


def create_document_plan(
    source: str,
    instructions: str,
    model: BaseChatModel,
) -> DocumentPlan:
    """Ask the selected model for schema-validated editorial output."""
    structured_model = model.with_structured_output(DocumentPlan)
    try:
        result = structured_model.invoke(build_messages(source, instructions))
    except Exception as exc:
        raise safe_provider_error(exc) from exc
    return result if isinstance(result, DocumentPlan) else DocumentPlan.model_validate(result)


def create_pdf_from_text(
    typed_text: str,
    uploaded_text: str,
    instructions: str,
    provider: Provider,
    api_key: str,
    *,
    model_name: str | None = None,
    model: BaseChatModel | None = None,
) -> tuple[bytes, DocumentPlan]:
    """Validate, plan, and render a document without persisting inputs or credentials."""
    source = combine_source_text(typed_text, uploaded_text)
    direction = validate_instructions(instructions)
    active_model = model or build_chat_model(provider, api_key, model_name)
    plan = create_document_plan(source, direction, active_model)
    return render_document(plan), plan


def create_pdf_from_sources(
    typed_text: str,
    uploads: Sequence[SourceUpload],
    youtube_urls: Sequence[str],
    instructions: str,
    provider: Provider,
    api_key: str,
    model_name: str,
    *,
    progress: ProgressReporter | None = None,
    model: BaseChatModel | None = None,
) -> tuple[bytes, DocumentPlan, PreparedSources]:
    """Ingest mixed sources, plan a document, and render the resulting PDF."""
    if progress is not None:
        progress("Preparing your sources...", 8)
    prepared = prepare_source_text(
        typed_text,
        uploads,
        youtube_urls,
        provider,
        api_key,
        model_name,
        progress=progress,
    )
    direction = validate_instructions(instructions)

    if progress is not None:
        progress(f"Asking {provider.value} to organize the document...", 72)
    active_model = model or build_chat_model(provider, api_key, model_name)
    plan = create_document_plan(prepared.source, direction, active_model)

    if progress is not None:
        progress("Rendering the PDF layout...", 92)
    return render_document(plan), plan, prepared
