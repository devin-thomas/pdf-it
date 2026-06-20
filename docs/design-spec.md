# pdf-it design specification

The accepted primary concept is `docs/pdf-it-dark-concept.png` at 1536 x 1024.

## Visual system

- Native dark background: `#0c0d0f`; raised surface: `#15171b`.
- Warm foreground: `#f2eee6`; muted copy: `#aaa7a1`; rule: `#303238`.
- Cobalt action and focus color: `#2f6df6`.
- Display typography: high-contrast editorial serif. UI typography: clean humanist sans.
- Open two-column desktop composition, with the writing surface taking roughly two thirds.
- Restrained corners, crisp one-pixel rules, generous spacing, and no ornamental cards.

## Interaction inventory

- Two-sided light/dark theme switch with native color-scheme metadata and a Dark Reader lock signal.
- Source text area with a live 30,000-character editor limit plus mixed-file uploads up to 10 MB each.
- Optional creative-direction field.
- Gemini, OpenAI, and Claude provider selector with masked API-key input and a compact Gemini help affordance.
- Gemini key setup link, session-only privacy note, generate action, and PDF download state.
- Mobile layout collapses to one column without horizontal overflow.

## Visible-copy lock

- pdf-it
- Turn plain text into a document worth sharing.
- Source text
- Creative direction (optional)
- AI provider
- API key
- Get a free Gemini API key
- Create PDF

The implementation may add concise validation and status messages required by the workflow.
