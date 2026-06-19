# Verification record

Last verified: June 19, 2026

## Automated checks

- `python -m ruff check .`: passed.
- `python -m pytest --cov=pdf_it --cov-fail-under=90`: 17 tests passed.
- Core package statement coverage: 96%.
- `python -m pip check`: no broken requirements.
- Tracked-file credential scan: no supplied test credential or private-key material found.
- A clean Python 3.12.3 environment installed the pinned dependency set and passed every check.

## Live provider check

A real Gemini request was executed with a temporary process-only credential against
`gemini-3.5-flash`. The production workflow completed all of these stages:

1. Provider client construction through `langchain-google-genai`.
2. Schema-constrained `DocumentPlan` generation.
3. In-memory ReportLab PDF rendering.
4. PDF parsing and page-count validation with pypdf.
5. Full-page visual rendering and inspection.

The check produced a valid one-page PDF without persisting the credential. OpenAI and Anthropic
are covered by provider-routing tests but require account-specific live keys for equivalent smoke
tests.

## Visual checks

- The accepted interface concept is `docs/pdf-it-dark-concept.png`.
- The live Streamlit app was inspected in the in-app browser at a 1280 x 720 desktop viewport.
- Layout, visible copy, native dark palette, writing surface, provider controls, focus treatment,
  upload surface, privacy copy, and disabled action state were compared to the concept.
- One mismatch was found: Streamlit's heading font overrode the editorial serif. The selector was
  strengthened, and the provider-selected state was brought closer to the concept.
- A post-fix localhost reload was blocked by the browser URL policy. Streamlit's application test
  harness reran successfully after the fix; the remaining risk is limited to post-fix screenshot
  recapture.

## External deployment evidence still required

- GitHub Actions after the first push. The equivalent Python 3.12 commands pass locally.
- Streamlit Community Cloud build and public URL smoke test.
- Live OpenAI and Anthropic checks when suitable test keys are available.
