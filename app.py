"""Streamlit entrypoint for the pdf-it document generator."""

# Embedded CSS is intentionally kept beside its selectors for easier visual maintenance.
# ruff: noqa: E501

from __future__ import annotations

import re

import streamlit as st

from pdf_it.config import (
    MAX_INSTRUCTIONS_CHARACTERS,
    MAX_SOURCE_CHARACTERS,
    MAX_SOURCE_UPLOADS,
    MAX_UPLOAD_BYTES,
    MAX_YOUTUBE_LINKS,
    PROVIDER_CONFIGS,
    Provider,
)
from pdf_it.ingestion import SourceUpload
from pdf_it.providers import ProviderRequestError
from pdf_it.service import create_pdf_from_sources
from pdf_it.validation import InputValidationError

st.set_page_config(
    page_title="pdf-it - AI document studio",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="collapsed",
)

UPLOAD_SIZE_MB = MAX_UPLOAD_BYTES // 1_000_000
UPLOAD_FORMAT_SUMMARY = (
    "TXT • MD • Markdown • MDX • PDF • DOCX • GDOC • CSV • XLSX • code • audio"
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
        .block-container {{ max-width: 1360px; padding: 1.15rem 3rem 2.5rem; }}
        h1, h2, h3, p, label, [data-testid='stCaptionContainer'] {{ color: var(--ts-text); }}
        h1, h2, h3 {{ font-family: 'Libre Caslon Display', Georgia, serif; letter-spacing: -.025em; }}
        .ts-brand {{
            font-family: 'Libre Caslon Display', Georgia, serif;
            color: var(--ts-text);
            font-size: 2rem;
            line-height: 1;
            letter-spacing: -.035em;
        }}
        .ts-theme-label {{
            color: var(--ts-muted);
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .12em;
            text-transform: uppercase;
            line-height: 1;
        }}
        .ts-theme-label.is-active {{
            color: var(--ts-text);
        }}
        .stVerticalBlock.st-key-theme-switch-row {{
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-end !important;
            align-items: center !important;
            gap: .7rem;
            flex-wrap: nowrap !important;
        }}
        .stVerticalBlock.st-key-theme-switch-row > div {{
            width: auto !important;
            flex: 0 0 auto !important;
        }}
        .ts-rule {{ border: 0; border-top: 1px solid var(--ts-rule); margin: .65rem 0 1.8rem; }}
        .ts-hero h1 {{
            color: var(--ts-text);
            font-family: 'Libre Caslon Display', Georgia, serif;
            font-weight: 400;
            font-size: clamp(2.35rem, 4.5vw, 4.45rem);
            line-height: 1.03;
            max-width: 760px;
            margin: 0 0 .7rem;
        }}
        .ts-hero p {{ color: var(--ts-muted); font-size: 1rem; max-width: 640px; margin-bottom: 1.45rem; }}
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
        [data-testid='stTextInput'] input,
        [data-testid='stSelectbox'] div[data-baseweb='select'] > div {{
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
            min-height: 6.6rem;
        }}
        [data-testid='stFileUploaderDropzone'] button {{ color: var(--ts-text); border-color: var(--ts-rule); }}
        [data-testid='stRadio'] > div {{ gap: 0; }}
        [data-testid='stRadio'] label {{
            background: var(--ts-surface);
            border: 1px solid var(--ts-rule);
            margin-right: -1px;
            min-height: 4.1rem;
            padding: .72rem .9rem;
        }}
        [data-testid='stRadio'] label:first-child {{ border-radius: .45rem 0 0 .45rem; }}
        [data-testid='stRadio'] label:last-child {{ border-radius: 0 .45rem .45rem 0; }}
        [data-testid='stRadio'] p {{ font-weight: 600; }}
        [data-testid='stRadio'] label:has(input:checked) {{
            background: var(--ts-accent);
            border-color: var(--ts-accent);
        }}
        [data-testid='stRadio'] label:has(input:checked) p {{ color: white; }}
        .st-key-theme-dark-enabled {{
            display: flex;
            justify-content: center;
        }}
        .st-key-theme-dark-enabled label[data-baseweb='checkbox'] {{
            min-height: 2rem;
        }}
        .st-key-theme-dark-enabled div[data-testid='stWidgetLabel'] {{
            display: none;
        }}
        .st-key-theme-dark-enabled [data-baseweb='checkbox'] > div:first-child {{
            background: rgba(255,255,255,.10);
            border: 0;
            width: 3rem;
            height: 1.8rem;
            border-radius: 999px;
            transition: background-color .18s ease;
        }}
        .st-key-theme-dark-enabled [data-baseweb='checkbox'] input:checked + div,
        .st-key-theme-dark-enabled [data-baseweb='checkbox'][aria-checked='true'] > div:first-child {{
            background: var(--ts-accent);
        }}
        .st-key-theme-dark-enabled [data-baseweb='checkbox'] > div:first-child > div {{
            width: 1.3rem;
            height: 1.3rem;
            background: #f2eee6;
            border: 0;
        }}
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
        .st-key-gemini-help-open button,
        .st-key-gemini-help-close button {{
            min-height: 2.15rem;
            width: 2.15rem;
            border-radius: 999px;
            padding: 0;
            font-size: .82rem;
            font-weight: 700;
            color: var(--ts-muted);
        }}
        .st-key-gemini-help-open button:hover,
        .st-key-gemini-help-close button:hover {{
            color: var(--ts-text);
        }}
        .st-key-gemini-help-done button {{ min-height: 3.2rem; font-weight: 700; }}
        .ts-help-note {{
            color: var(--ts-muted);
            font-size: .92rem;
            line-height: 1.55;
        }}
        .ts-progress-note {{
            color: var(--ts-muted);
            font-size: .86rem;
            margin-top: .3rem;
        }}
        details[data-testid='stExpander'] {{
            border: 1px solid var(--ts-rule);
            border-radius: .45rem;
            background: rgba(255,255,255,.02);
            margin-top: .55rem;
        }}
        details[data-testid='stExpander'] summary {{
            padding: .8rem 1rem;
        }}
        details[data-testid='stExpander'] > div {{
            padding: 0 .95rem .9rem;
        }}
        div[data-testid='stAlert'] {{ background: var(--ts-surface-2); border-color: var(--ts-rule); color: var(--ts-text); }}
        @media (max-width: 800px) {{
            .block-container {{ padding: .9rem 1rem 1.7rem; }}
            .ts-brand {{ font-size: 1.85rem; }}
            .ts-theme-label {{ font-size: .64rem; letter-spacing: .08em; }}
            .st-key-theme-switch-row {{ gap: .55rem; }}
            .ts-rule {{ margin: .45rem 0 1.2rem; }}
            .ts-hero h1 {{ font-size: 2.15rem; margin-bottom: .5rem; }}
            .ts-hero p {{ font-size: .98rem; margin-bottom: 1rem; }}
            [data-testid='stTextArea'] textarea {{ min-height: 8.75rem !important; }}
            [data-testid='stFileUploaderDropzone'] {{ min-height: 5rem; }}
            [data-testid='stRadio'] label {{ min-height: 3.35rem; padding: .58rem .7rem; }}
            [data-testid='stColumn']:has(.ts-rail-marker) {{ border-left: 0; border-top: 1px solid var(--ts-rule); padding: 1rem 0 0; margin-top: .65rem; }}
            .ts-footer {{ gap: 1rem; align-items: flex-start; flex-direction: column; }}
        }}
        @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Dark Reader checks for this lock; the root CSS color-scheme styles native controls.
    st.html(
        f'<meta name="darkreader-lock" content="pdf-it provides a native {theme} theme.">'
    )


def safe_filename(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    return f"{slug or 'pdf-it-document'}.pdf"


@st.dialog("Get a Gemini API key")
def show_gemini_help_dialog() -> None:
    _, close_column = st.columns([8, 1], vertical_alignment="center")
    with close_column:
        if st.button("X", key="gemini-help-close", help="Close this help pop-up."):
            st.session_state.show_gemini_help = False
            st.rerun()

    st.markdown(
        "1. Open Google AI Studio from the Gemini key button.\n"
        "2. Sign in with the Google account you want to use for Gemini API access.\n"
        "3. Go to the **API keys** page and choose **Create API key**.\n"
        "4. If Google asks you to choose a project, pick the one you want the key tied to.\n"
        "5. Copy the key that starts with `AIza` and paste it into pdf-it."
    )
    st.markdown(
        """
        <div class="ts-help-note">
        Free-tier Gemini API usage is subject to Google's data collection and provider terms, so do not
        send content your Google account is not permitted to process.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Google's official Gemini API key help",
        PROVIDER_CONFIGS[Provider.GEMINI].help_url,
        use_container_width=True,
    )
    if st.button("Done", key="gemini-help-done", type="primary", use_container_width=True):
        st.session_state.show_gemini_help = False
        st.rerun()


if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "theme_dark_enabled" not in st.session_state:
    st.session_state.theme_dark_enabled = st.session_state.theme == "dark"
if "show_gemini_help" not in st.session_state:
    st.session_state.show_gemini_help = False

header_left, header_right = st.columns([7.4, 2.6], vertical_alignment="center")
with header_left:
    st.markdown('<div class="ts-brand">pdf-it</div>', unsafe_allow_html=True)
with header_right:
    with st.container(key="theme-switch-row"):
        st.markdown(
            f'<div class="ts-theme-label {"is-active" if not st.session_state.theme_dark_enabled else ""}">Light</div>',
            unsafe_allow_html=True,
        )
        st.toggle("Theme mode", key="theme_dark_enabled", label_visibility="collapsed")
        st.markdown(
            f'<div class="ts-theme-label {"is-active" if st.session_state.theme_dark_enabled else ""}">Dark</div>',
            unsafe_allow_html=True,
        )
    st.session_state.theme = "dark" if st.session_state.theme_dark_enabled else "light"

install_theme(st.session_state.theme)
if st.session_state.show_gemini_help:
    show_gemini_help_dialog()
st.markdown('<hr class="ts-rule">', unsafe_allow_html=True)
st.html(
    """
    <section class="ts-hero">
      <h1>Turn plain text into a document worth sharing.</h1>
      <p>Add your source, shape the direction, and let AI organize it into a polished PDF.</p>
    </section>
    """
)

editor, rail = st.columns([1.72, 0.88], gap="large", vertical_alignment="top")

with editor:
    typed_text = st.text_area(
        "Source text",
        height=220,
        max_chars=MAX_SOURCE_CHARACTERS,
        placeholder="Paste your text here...",
        help=(
            "Typed text has its own 30,000-character editor limit. Uploaded files and "
            "transcripts are processed separately and may be trimmed later if the "
            "combined working source exceeds the model budget."
        ),
    )
    st.caption(f"{len(typed_text):,} / {MAX_SOURCE_CHARACTERS:,} typed characters")
    uploaded_files = st.file_uploader(
        "Add source files",
        accept_multiple_files=True,
        max_upload_size=UPLOAD_SIZE_MB,
        help=(
            "Mix up to 5 files: TXT, MD, Markdown, MDX, PDF, DOCX, GDOC, CSV, "
            "XLSX, common code files, or audio for transcription. Each file can be up "
            "to 10 MB."
        ),
    )
    st.caption(
        f"{len(uploaded_files)} / {MAX_SOURCE_UPLOADS} files selected • {UPLOAD_SIZE_MB} MB each • {UPLOAD_FORMAT_SUMMARY}"
    )
    with st.expander("YouTube transcript links or IDs (optional)", expanded=False):
        youtube_links = st.text_area(
            "YouTube transcript links or IDs (optional)",
            height=96,
            placeholder="Paste up to 5 YouTube links or 11-character video IDs, one per line...",
            help=(
                "pdf-it will try to pull public captions or auto-generated transcripts "
                "from the provided YouTube links or video IDs."
            ),
            label_visibility="collapsed",
        )
        st.caption(
            f"Up to {MAX_YOUTUBE_LINKS} YouTube links or video IDs can be imported per document."
        )
    with st.expander("Creative direction (optional)", expanded=False):
        instructions = st.text_area(
            "Creative direction (optional)",
            height=116,
            max_chars=MAX_INSTRUCTIONS_CHARACTERS,
            placeholder="Describe the audience, tone, structure, or emphasis...",
            label_visibility="collapsed",
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
    model_options = provider_config.models
    default_model_index = next(
        index
        for index, option in enumerate(model_options)
        if option.id == provider_config.default_model
    )
    selected_model = st.selectbox(
        "Model",
        options=model_options,
        index=default_model_index,
        format_func=lambda option: option.label,
        key=f"{selected_provider.value.lower()}-model",
    )
    st.caption(selected_model.description)
    if selected_provider is Provider.GEMINI:
        key_link, help_button = st.columns([5.3, 0.75], gap="small", vertical_alignment="center")
        with key_link:
            st.link_button(
                "Get a free Gemini API key",
                provider_config.key_help_url,
                help="Opens Google AI Studio in a new tab.",
                use_container_width=True,
            )
        with help_button:
            if st.button("?", key="gemini-help-open", help="How to get a Gemini API key."):
                st.session_state.show_gemini_help = True
                st.rerun()
    else:
        st.link_button(
            f"Manage {selected_provider.value} API keys",
            provider_config.key_help_url,
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="ts-privacy">
        Your key stays in this active Streamlit session and is sent only to the provider you
        select. pdf-it does not write keys, source text, or generated PDFs to disk.
        </div>
        """,
        unsafe_allow_html=True,
    )

    youtube_url_list = [line.strip() for line in youtube_links.splitlines() if line.strip()]
    has_source = bool(typed_text.strip() or uploaded_files or youtube_url_list)
    create_clicked = st.button(
        "Create PDF",
        type="primary",
        use_container_width=True,
        disabled=not (has_source and api_key.strip()),
    )
    if not has_source or not api_key.strip():
        st.caption("Add source text and an API key to get started.")

if create_clicked:
    progress_bar = st.progress(0, text="Preparing your document request...")
    progress_note = st.empty()

    def report_progress(message: str, percent: int) -> None:
        progress_bar.progress(min(max(percent, 1), 100), text=message)
        progress_note.markdown(
            f'<div class="ts-progress-note">{message}</div>',
            unsafe_allow_html=True,
        )

    try:
        uploads = [
            SourceUpload(name=uploaded.name, data=uploaded.getvalue()) for uploaded in uploaded_files
        ]
        pdf_bytes, plan, _prepared = create_pdf_from_sources(
            typed_text,
            uploads,
            youtube_url_list,
            instructions,
            selected_provider,
            api_key,
            selected_model.id,
            progress=report_progress,
        )
        st.session_state.generated_pdf = pdf_bytes
        st.session_state.generated_filename = safe_filename(plan.title)
        st.session_state.generated_title = plan.title
        progress_bar.progress(100, text="PDF ready.")
        progress_note.markdown(
            '<div class="ts-progress-note">The source review, AI planning, and PDF rendering are complete.</div>',
            unsafe_allow_html=True,
        )
    except (InputValidationError, ProviderRequestError) as exc:
        progress_bar.empty()
        progress_note.empty()
        st.error(str(exc))
    except Exception:
        progress_bar.empty()
        progress_note.empty()
        # Unexpected details can include SDK internals, so the UI intentionally stays generic.
        st.error("pdf-it could not finish this document. Please try again.")

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
      <span>pdf-it - private by design, provider processing applies.</span>
      <span>Built with Streamlit, LangChain, and ReportLab.</span>
    </footer>
    """,
    unsafe_allow_html=True,
)
