"""LangChain provider adapters with no global credential state."""

from langchain_core.language_models.chat_models import BaseChatModel

from .config import PROVIDER_CONFIGS, Provider


class ProviderRequestError(RuntimeError):
    """A safe, user-facing provider failure that never includes credentials."""


def build_chat_model(
    provider: Provider,
    api_key: str,
    model_name: str | None = None,
) -> BaseChatModel:
    """Build a short-lived client using the key supplied for this session only."""
    if not api_key.strip():
        raise ProviderRequestError("Enter an API key for the selected provider.")

    resolved_model = model_name or PROVIDER_CONFIGS[provider].default_model

    # Imports stay local so a missing optional provider package reports at selection time.
    if provider is Provider.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=resolved_model,
            api_key=api_key.strip(),
            temperature=1.0,
            max_retries=2,
            timeout=60,
        )
    if provider is Provider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=resolved_model,
            api_key=api_key.strip(),
            max_retries=2,
            timeout=60,
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=resolved_model,
        api_key=api_key.strip(),
        max_retries=2,
        timeout=60,
    )


def safe_provider_error(exc: Exception) -> ProviderRequestError:
    """Map SDK details to actionable categories without reflecting raw messages."""
    message = str(exc).lower()
    if any(term in message for term in ("api key", "authentication", "unauthorized", "401")):
        detail = "The provider rejected that API key. Check the key and provider selection."
    elif (
        "model" in message
        and any(
            term in message
            for term in ("access", "permission", "unsupported", "not found", "does not exist")
        )
    ):
        detail = (
            "That API key does not have access to the selected model. "
            "Pick another model or key."
        )
    elif any(term in message for term in ("rate limit", "quota", "429")):
        detail = "The provider rate limit or quota was reached. Wait briefly or check billing."
    elif any(term in message for term in ("timeout", "timed out")):
        detail = "The provider took too long to respond. Please try again."
    else:
        detail = (
            "Your source import may have succeeded, but the provider could not create "
            "the document plan. Please try again."
        )
    return ProviderRequestError(detail)
