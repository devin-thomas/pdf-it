"""Input validation kept outside Streamlit so it remains easy to test."""

from .config import (
    MAX_INSTRUCTIONS_CHARACTERS,
    MAX_SOURCE_CHARACTERS,
    MAX_UPLOAD_BYTES,
)


class InputValidationError(ValueError):
    """A user-correctable input problem."""


def decode_text_upload(data: bytes) -> str:
    """Decode a small UTF-8 text upload without guessing legacy encodings."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise InputValidationError("The uploaded file must be 1 MB or smaller.")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputValidationError("The uploaded file must use UTF-8 text encoding.") from exc


def combine_source_text(typed_text: str, uploaded_text: str = "") -> str:
    """Combine both intentional input paths while enforcing one clear budget."""
    parts = [part.strip() for part in (typed_text, uploaded_text) if part.strip()]
    source = "\n\n".join(parts)
    if not source:
        raise InputValidationError("Add source text or upload a TXT file.")
    if len(source) > MAX_SOURCE_CHARACTERS:
        raise InputValidationError(
            f"Source text must be {MAX_SOURCE_CHARACTERS:,} characters or fewer."
        )
    return source


def validate_instructions(instructions: str) -> str:
    instructions = instructions.strip()
    if len(instructions) > MAX_INSTRUCTIONS_CHARACTERS:
        raise InputValidationError(
            f"Creative direction must be {MAX_INSTRUCTIONS_CHARACTERS:,} characters or fewer."
        )
    return instructions
