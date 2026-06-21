from pdf_it.prompts import SYSTEM_PROMPT, build_messages


def test_system_prompt_requires_code_aware_block_output() -> None:
    assert "treat those sections as code, not prose" in SYSTEM_PROMPT
    assert 'code blocks as {kind: "code", text: "..."}' in SYSTEM_PROMPT


def test_build_messages_keeps_source_and_direction_boundaries() -> None:
    messages = build_messages("print('hello')", "Keep prose concise.")

    assert messages[0].content == SYSTEM_PROMPT
    assert "<SOURCE>\nprint('hello')\n</SOURCE>" in messages[1].content
    assert "<CREATIVE_DIRECTION>\nKeep prose concise.\n</CREATIVE_DIRECTION>" in (
        messages[1].content
    )
