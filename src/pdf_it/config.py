"""Application-wide limits and provider metadata."""

from dataclasses import dataclass
from enum import StrEnum

MAX_SOURCE_CHARACTERS = 30_000
MAX_INSTRUCTIONS_CHARACTERS = 1_500
MAX_UPLOAD_BYTES = 10_000_000
MAX_SOURCE_UPLOADS = 5
MAX_YOUTUBE_LINKS = 5
MAX_DATAFRAME_ROWS = 40
MAX_DATAFRAME_COLUMNS = 18


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    description: str


class Provider(StrEnum):
    GEMINI = "Gemini"
    OPENAI = "OpenAI"
    ANTHROPIC = "Claude"


@dataclass(frozen=True)
class ProviderConfig:
    default_model: str
    models: tuple[ModelOption, ...]
    key_prefix: str
    key_help_url: str
    help_url: str
    transcription_model: str | None = None


PROVIDER_CONFIGS = {
    Provider.GEMINI: ProviderConfig(
        default_model="gemini-3.1-flash-lite",
        models=(
            ModelOption(
                id="gemini-3.1-flash-lite",
                label="Gemini 3.1 Flash Lite",
                description="Default Gemini option for fast, lower-cost document shaping.",
            ),
            ModelOption(
                id="gemini-3.5-flash",
                label="Gemini 3.5 Flash",
                description=(
                    "Higher-quality Gemini flash model for broader mixed-source"
                    " packets."
                ),
            ),
            ModelOption(
                id="gemini-2.5-pro",
                label="Gemini 2.5 Pro",
                description=(
                    "Higher-reasoning Gemini model for dense or complex source packets."
                ),
            ),
            ModelOption(
                id="gemini-3.1-pro-preview",
                label="Gemini 3.1 Pro Preview",
                description=(
                    "Preview Gemini model with stronger reasoning but stricter access"
                    " limits."
                ),
            ),
        ),
        key_prefix="AIza",
        key_help_url="https://aistudio.google.com/app/apikey",
        help_url="https://ai.google.dev/gemini-api/docs/api-key",
    ),
    Provider.OPENAI: ProviderConfig(
        default_model="gpt-5.4-mini",
        models=(
            ModelOption(
                id="gpt-5.5",
                label="GPT-5.5",
                description=(
                    "Highest-capability OpenAI option for longer or more demanding"
                    " inputs."
                ),
            ),
            ModelOption(
                id="gpt-5.4-mini",
                label="GPT-5.4 mini",
                description="Balanced default with strong speed, price, and quality.",
            ),
            ModelOption(
                id="gpt-5.4-nano",
                label="GPT-5.4 nano",
                description=(
                    "Fastest low-cost option for simple source cleanup and layout"
                    " planning."
                ),
            ),
        ),
        key_prefix="sk-",
        key_help_url="https://platform.openai.com/api-keys",
        help_url="https://developers.openai.com/api/docs/models",
        transcription_model="gpt-4o-mini-transcribe",
    ),
    Provider.ANTHROPIC: ProviderConfig(
        default_model="claude-sonnet-4-6",
        models=(
            ModelOption(
                id="claude-haiku-4-5",
                label="Claude Haiku 4.5",
                description="Fastest Claude option for lighter source material.",
            ),
            ModelOption(
                id="claude-sonnet-4-6",
                label="Claude Sonnet 4.6",
                description="Best general-purpose Claude model for polished document plans.",
            ),
            ModelOption(
                id="claude-opus-4-8",
                label="Claude Opus 4.8",
                description="Highest-capability Claude option for dense or nuanced inputs.",
            ),
        ),
        key_prefix="sk-ant-",
        key_help_url="https://console.anthropic.com/settings/keys",
        help_url="https://platform.claude.com/docs/en/about-claude/models/overview",
    ),
}
