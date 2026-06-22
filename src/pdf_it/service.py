"""Orchestration boundary between user input, LangChain, and PDF rendering."""

import re
from collections.abc import Callable, Sequence
from dataclasses import replace

from langchain_core.language_models.chat_models import BaseChatModel

from .config import Provider
from .ingestion import (
    PreparedSources,
    SourceUpload,
    extract_youtube_video_id,
    prepare_source_text,
)
from .pdf_renderer import render_document
from .prompts import build_messages
from .providers import ProviderRequestError, build_chat_model, safe_provider_error
from .schemas import DocumentBlock, DocumentPlan, DocumentSection
from .validation import combine_source_text, validate_instructions

ProgressReporter = Callable[[str, int], None]
SOURCE_HEADER_PATTERN = re.compile(r"(?m)^\[Source: (?P<label>.+)]\n")
LOCAL_BLOCK_CHARACTERS = 7_000


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


def create_source_preserving_plan(
    source: str,
    youtube_urls: Sequence[str],
) -> DocumentPlan:
    """Build a valid local plan when an imported transcript cannot reach the provider."""
    matches = list(SOURCE_HEADER_PATTERN.finditer(source))
    sections: list[DocumentSection] = []

    if matches:
        sources = [
            (
                match.group("label").strip(),
                source[
                    match.end() : (
                        matches[index + 1].start() if index + 1 < len(matches) else None
                    )
                ],
            )
            for index, match in enumerate(matches)
        ]
    else:
        sources = [("Transcript", source)]

    for label, text in sources:
        blocks = [
            DocumentBlock(kind="paragraph", text=chunk)
            for chunk in _chunk_source_text(text)
        ]
        sections.append(
            DocumentSection(
                heading=(label or "Transcript")[:120],
                blocks=blocks,
            )
        )

    video_ids = [
        video_id
        for value in youtube_urls
        if (video_id := extract_youtube_video_id(value)) is not None
    ]
    title = "YouTube Transcript" if len(video_ids) == 1 else "YouTube Transcripts"
    subtitle = (
        f"Video ID: {video_ids[0]}"
        if len(video_ids) == 1
        else f"Video IDs: {', '.join(video_ids)}"
    )
    return DocumentPlan(
        title=title,
        subtitle=subtitle,
        summary=(
            "Captions imported from YouTube and rendered locally. The transcript wording "
            "below is preserved from the available public caption track."
        ),
        sections=sections,
    )


def _chunk_source_text(text: str) -> list[str]:
    """Fit source text into schema blocks without dropping transcript content."""
    remaining = text.strip()
    chunks: list[str] = []
    while len(remaining) > LOCAL_BLOCK_CHARACTERS:
        split_at = remaining.rfind("\n", 0, LOCAL_BLOCK_CHARACTERS)
        if split_at < LOCAL_BLOCK_CHARACTERS // 2:
            split_at = remaining.rfind(" ", 0, LOCAL_BLOCK_CHARACTERS)
        if split_at < 1:
            split_at = LOCAL_BLOCK_CHARACTERS
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks or ["No transcript text was returned."]


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

    use_local_plan = bool(youtube_urls) and not api_key.strip() and model is None
    if use_local_plan:
        if progress is not None:
            progress("Rendering the imported transcript locally...", 78)
        plan = create_source_preserving_plan(prepared.source, youtube_urls)
    else:
        if progress is not None:
            progress(f"Asking {provider.value} to organize the document...", 72)
        try:
            active_model = model or build_chat_model(provider, api_key, model_name)
            plan = create_document_plan(prepared.source, direction, active_model)
        except ProviderRequestError:
            if not youtube_urls:
                raise
            use_local_plan = True
            if progress is not None:
                progress("Provider unavailable; preserving the transcript locally...", 78)
            plan = create_source_preserving_plan(prepared.source, youtube_urls)

    if use_local_plan:
        prepared = replace(prepared, used_local_plan=True)

    if progress is not None:
        progress("Rendering the PDF layout...", 92)
    return render_document(plan), plan, prepared
