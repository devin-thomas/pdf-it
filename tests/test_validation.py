import pytest

from typeset.config import MAX_INSTRUCTIONS_CHARACTERS, MAX_SOURCE_CHARACTERS, MAX_UPLOAD_BYTES
from typeset.validation import (
    InputValidationError,
    combine_source_text,
    decode_text_upload,
    validate_instructions,
)


def test_combines_typed_and_uploaded_text() -> None:
    assert combine_source_text(" Typed ", " Uploaded ") == "Typed\n\nUploaded"


@pytest.mark.parametrize("typed, uploaded", [("", ""), ("  ", "\n")])
def test_requires_at_least_one_source(typed: str, uploaded: str) -> None:
    with pytest.raises(InputValidationError, match="Add source"):
        combine_source_text(typed, uploaded)


def test_rejects_combined_source_over_limit() -> None:
    with pytest.raises(InputValidationError, match="5,000"):
        combine_source_text("x" * MAX_SOURCE_CHARACTERS, "one extra character")


def test_decodes_utf8_bom_and_rejects_invalid_uploads() -> None:
    assert decode_text_upload(b"\xef\xbb\xbfHello") == "Hello"
    with pytest.raises(InputValidationError, match="UTF-8"):
        decode_text_upload(b"\xff\xfe")
    with pytest.raises(InputValidationError, match="1 MB"):
        decode_text_upload(b"x" * (MAX_UPLOAD_BYTES + 1))


def test_instruction_limit() -> None:
    assert validate_instructions(" concise ") == "concise"
    with pytest.raises(InputValidationError, match="Creative direction"):
        validate_instructions("x" * (MAX_INSTRUCTIONS_CHARACTERS + 1))
