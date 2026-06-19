"""Streamlit entrypoint for the Typeset document generator."""

# Embedded CSS is intentionally kept beside its selectors for easier visual maintenance.
# ruff: noqa: E501

from __future__ import annotations

import re

import streamlit as st

from typeset.config import (
    MAX_INSTRUCTIONS_CHARACTERS,
    MAX_SOURCE_CHARACTERS,
    PROVIDER_CONFIGS,
    Provider,
)
from typeset.providers import ProviderRequestError
from typeset.service import create_pdf_from_text
from typeset.validation import InputValidationError, decode_text_upload

st.set_page_config(
    page_title="Typeset - AI document studio",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def install_theme(theme: str) -> None:
    """Install the visual tokens and signal that this is a genuine native theme."""
    is_dark = theme == "dark"
    palette = {
        "bg": "#0c0d0f" if is_dark else "#f7f6f2",
        "surface": "#15171b" if is_dark else "#ffffff",
        "surface_2": "#111318" if is_dark else "#eef2fa",
        "text": "#f2eee6" if is_dark else "#182033",
        "muted": "#aaa7a1" if is_dark else "#647086",
        "rule": "#303238" if is_dark else "#d8dde7",
        "field": "#111316" if is_dark else "#ffffff",
        "accent": "#2f6df6",
    }
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Libre+Caslon+Display&display=swap');

        :root {{ color-scheme: {theme}; }}
        .stApp {{
            --ts-bg: {palette['bg']};
            --ts-surface: {palette['surface']};
            --ts-surface-2: {palette['surface_2']};
            --ts-text: {palette['text']};
            --ts-muted: {palette['muted']};
            --ts-rule: {palette['rule']};
            --ts-field: {palette['field']};
            --ts-accent: {palette['accent']};
            background:
                radial-gradient(circle at 15% -10%, rgba(47,109,246,.08), transparent 29rem),
                var(--ts-bg);
            color: var(--ts-text);
            font-family: 'DM Sans', sans-serif;
            transition: background-color .18s ease, color .18s ease;
        }}
        .stApp::before {{
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: {'.16' if is_dark else '.055'};
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.18'/%3E%3C/svg%3E");
        }}
        [data-testid='stHeader'] {{ background: transparent; }}
        [data-testid='stToolbar'] {{ visibility: hidden; }}
        [data-testid='stAppViewContainer'] > .main {{ background: transparent; }}
        .block-container {{ max-width: 1360px; padding: 2rem 3rem 2.5rem; }}
        h1, h2, h3, p, label, [data-testid='stCaptionContainer'] {{ color: var(--ts-text); }}
        h1, h2, h3 {{ font-family: 'Libre Caslon Display', Georgia, serif; letter-spacing: -.025em; }}
        .ts-brand {{
            font-family: 'Libre Caslon Display', Georgia, serif;
            color: var(--ts-text);
            font-size: 2rem;
            line-height: 1;
            letter-spacing: -.035em;
        }}
        .ts-rule {{ border: 0; border-top: 1px solid var(--ts-rule); margin: 1.1rem 0 2.6rem; }}
        .ts-hero h1 {{
            color: var(--ts-text);
            font-family: 'Libre Caslon Display', Georgia, serif;
            font-weight: 400;
            font-size: clamp(2.8rem, 5.2vw, 5.2rem);
            line-height: 1.01;
            max-width: 900px;
            margin: 0 0 1rem;
        }}
        .ts-hero p {{ color: var(--ts-muted); font-size: 1.06rem; max-width: 720px; margin-bottom: 2.4rem; }}
        .ts-section-label {{
            color: var(--ts-muted);
            font-size: .72rem;
            font-weight: 600;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: .25rem 0 .85rem;
        }}
        [data-testid='stColumn']:has(.ts-rail-marker) {{
            border-left: 1px solid var(--ts-rule);
            padding-left: 2rem;
        }}
        .ts-rail-marker {{ display: none; }}
        .ts-privacy {{
            color: var(--ts-muted);
            font-size: .82rem;
            line-height: 1.55;
            border-top: 1px solid var(--ts-rule);
            padding-top: 1rem;
            margin-top: .6rem;
        }}
        .ts-footer {{
            border-top: 1px solid var(--ts-rule);
            color: var(--ts-muted);
            font-size: .76rem;
            margin-top: 3rem;
            padding-top: 1.2rem;
            display: flex;
            justify-content: space-between;
        }}
        [data-testid='stTextArea'] textarea,
        [data-testid='stTextInput'] input {{
            background: var(--ts-field);
            color: var(--ts-text);
            border: 1px solid var(--ts-rule);
            border-radius: .45rem;
            font-family: 'DM Sans', sans-serif;
        }}
        [data-testid='stTextArea'] textarea:focus,
        [data-testid='stTextInput'] input:focus {{
            border-color: var(--ts-accent);
            box-shadow: 0 0 0 1px var(--ts-accent);
        }}
        [data-testid='stFileUploaderDropzone'] {{
            background: var(--ts-surface-2);
            border: 1px dashed rgba(47,109,246,.78);
            border-radius: .45rem;
            min-height: 8rem;
        }}
        [data-testid='stFileUploaderDropzone'] button {{ color: var(--ts-text); border-color: var(--ts-rule); }}
        [data-testid='stRadio'] > div {{ gap: 0; }}
        [data-testid='stRadio'] label {{
            background: var(--ts-surface);
            border: 1px solid var(--ts-rule);
            margin-right: -1px;
            padding: .62rem .9rem;
        }}
        [data-testid='stRadio'] label:first-child {{ border-radius: .45rem 0 0 .45rem; }}
        [data-testid='stRadio'] label:last-child {{ border-radius: 0 .45rem .45rem 0; }}
        [data-testid='stRadio'] label:has(input:checked) {{
            background: var(--ts-accent);
            border-color: var(--ts-accent);
        }}
        [data-testid='stRadio'] label:has(input:checked) p {{ color: white; }}
        .stButton > button, .stDownloadButton > button {{
            min-height: 3.25rem;
            border-radius: .45rem;
            font-weight: 600;
            transition: transform .15s ease, box-shadow .15s ease;
        }}
        .stButton > button[kind='primary'], .stDownloadButton > button {{
            background: var(--ts-accent);
            border-color: var(--ts-accent);
            color: white;
            width: 100%;
        }}
        .stButton > button[kind='primary']:not(:disabled):hover,
        .stDownloadButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 8px 26px rgba(47,109,246,.23); }}
        .stLinkButton a {{ color: #5590ff; padding-left: 0; }}
        div[data-testid='stAlert'] {{ background: var(--ts-surface-2); border-color: var(--ts-rule); color: var(--ts-text); }}
        @media (max-width: 800px) {{
            .block-container {{ padding: 1.35rem 1.1rem 2rem; }}
            .ts-rule {{ margin-bottom: 1.8rem; }}
            .ts-hero h1 {{ font-size: 2.75rem; }}
            [data-testid='stColumn']:has(.ts-rail-marker) {{ border-left: 0; border-top: 1px solid var(--ts-rule); padding: 1.5rem 0 0; margin-top: 1rem; }}
            .ts-footer {{ gap: 1rem; align-items: flex-start; flex-direction: column; }}
        }}
        @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Dark Reader checks for this lock; the root CSS color-scheme styles native controls.
    st.html(
        f'<meta name="darkreader-lock" content="Typeset provides a native {theme} theme.">'
    )


def safe_filename(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    return f"{slug or 'typeset-document'}.pdf"


if "theme" not in st.session_state:
    st.session_state.theme = "dark"

header_left, header_right = st.columns([8, 2], vertical_alignment="center")
with header_left:
    st.markdown('<div class="ts-brand">Typeset</div>', unsafe_allow_html=True)
with header_right:
    light_mode = st.toggle("Light mode", value=st.session_state.theme == "light")
    st.session_state.theme = "light" if light_mode else "dark"

install_theme(st.session_state.theme)
st.markdown('<hr class="ts-rule">', unsafe_allow_html=True)
st.markdown(
    """
    <section class="ts-hero">
      <h1>Turn plain text into a document worth sharing.</h1>
      <p>Add your source, shape the direction, and let AI organize it into a polished PDF.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

editor, rail = st.columns([1.72, 0.88], gap="large", vertical_alignment="top")

with editor:
    typed_text = st.text_area(
        "Source text",
        height=270,
        max_chars=MAX_SOURCE_CHARACTERS,
        placeholder="Paste your text here...",
        help="Typed and uploaded text share the 5,000-character limit.",
    )
    st.caption(f"{len(typed_text):,} / {MAX_SOURCE_CHARACTERS:,} typed characters")
    uploaded_file = st.file_uploader(
        "Or add a TXT file",
        type=["txt"],
        accept_multiple_files=False,
        help="UTF-8 text only, up to 1 MB. If both inputs are present, they are combined.",
    )
    instructions = st.text_area(
        "Creative direction (optional)",
        height=128,
        max_chars=MAX_INSTRUCTIONS_CHARACTERS,
        placeholder="Describe the audience, tone, structure, or emphasis...",
    )

with rail:
    st.markdown('<span class="ts-rail-marker"></span>', unsafe_allow_html=True)
    st.markdown('<div class="ts-section-label">AI provider</div>', unsafe_allow_html=True)
    selected_provider = st.radio(
        "AI provider",
        options=list(Provider),
        format_func=lambda item: item.value,
        horizontal=True,
        label_visibility="collapsed",
    )
    provider_config = PROVIDER_CONFIGS[selected_provider]
    api_key = st.text_input(
        f"{selected_provider.value} API key",
        type="password",
        placeholder=f"Starts with {provider_config.key_prefix}",
        autocomplete="off",
    )
    if selected_provider is Provider.GEMINI:
        st.link_button(
            "Get a free Gemini API key",
            provider_config.key_help_url,
            help="Opens Google AI Studio in a new tab.",
        )
        with st.expander("How to get a free Gemini key"):
            st.markdown(
                "1. Open Google AI Studio with the link above.\n"
                "2. Sign in and choose **Create API key**.\n"
                "3. Copy it here. Review Google's current free-tier limits before use."
            )
    else:
        st.link_button(f"Manage {selected_provider.value} API keys", provider_config.key_help_url)

    st.markdown(
        """
        <div class="ts-privacy">
        Your key stays in this active Streamlit session and is sent only to the provider you
        select. Typeset does not write keys, source text, or generated PDFs to disk.
        </div>
        """,
        unsafe_allow_html=True,
    )

    has_source = bool(typed_text.strip() or uploaded_file)
    create_clicked = st.button(
        "Create PDF",
        type="primary",
        use_container_width=True,
        disabled=not (has_source and api_key.strip()),
    )
    if not has_source or not api_key.strip():
        st.caption("Add source text and an API key to get started.")

if create_clicked:
    try:
        uploaded_text = decode_text_upload(uploaded_file.getvalue()) if uploaded_file else ""
        with st.spinner(f"{selected_provider.value} is shaping your document..."):
            pdf_bytes, plan = create_pdf_from_text(
                typed_text,
                uploaded_text,
                instructions,
                selected_provider,
                api_key,
            )
        st.session_state.generated_pdf = pdf_bytes
        st.session_state.generated_filename = safe_filename(plan.title)
        st.session_state.generated_title = plan.title
    except (InputValidationError, ProviderRequestError) as exc:
        st.error(str(exc))
    except Exception:
        # Unexpected details can include SDK internals, so the UI intentionally stays generic.
        st.error("Typeset could not finish this document. Please try again.")

if st.session_state.get("generated_pdf"):
    st.success(f"{st.session_state.generated_title} is ready.")
    st.download_button(
        "Download PDF",
        data=st.session_state.generated_pdf,
        file_name=st.session_state.generated_filename,
        mime="application/pdf",
        use_container_width=True,
    )

st.markdown(
    """
    <footer class="ts-footer">
      <span>Typeset - private by design, provider processing applies.</span>
      <span>Built with Streamlit, LangChain, and ReportLab.</span>
    </footer>
    """,
    unsafe_allow_html=True,
)
