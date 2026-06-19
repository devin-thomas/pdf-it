"""Application-wide limits and provider metadata."""

from dataclasses import dataclass
from enum import StrEnum

MAX_SOURCE_CHARACTERS = 5_000
MAX_INSTRUCTIONS_CHARACTERS = 1_500
MAX_UPLOAD_BYTES = 1_000_000


class Provider(StrEnum):
    GEMINI = "Gemini"
    OPENAI = "OpenAI"
    ANTHROPIC = "Claude"


@dataclass(frozen=True)
class ProviderConfig:
    model: str
    key_prefix: str
    key_help_url: str


PROVIDER_CONFIGS = {
    Provider.GEMINI: ProviderConfig(
        model="gemini-3.5-flash",
        key_prefix="AIza",
        key_help_url="https://aistudio.google.com/app/apikey",
    ),
    Provider.OPENAI: ProviderConfig(
        model="gpt-5.4-mini",
        key_prefix="sk-",
        key_help_url="https://platform.openai.com/api-keys",
    ),
    Provider.ANTHROPIC: ProviderConfig(
        model="claude-sonnet-4-6",
        key_prefix="sk-ant-",
        key_help_url="https://console.anthropic.com/settings/keys",
    ),
}
